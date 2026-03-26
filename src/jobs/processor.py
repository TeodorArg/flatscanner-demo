"""End-to-end analysis job processor.

``process_job`` is the single function that drives a queued ``AnalysisJob``
through the full pipeline:

1. Resolve the adapter for the job's listing provider.
2. Fetch raw + normalised listing via the adapter (``AdapterResult``).
2a. Optionally persist the raw payload via ``raw_payload_repo`` (best-effort).
3. Run AI analysis through ``AnalysisService`` (canonical English output).
4. Translate freeform result blocks via ``TranslationService`` when the job
   language is not English.  Translated output is ephemeral and never persisted.
5. Format the translated result with ``format_analysis_message``.
6. Send the Telegram reply via ``send_message``.

Progress reporting is delegated to a ``ProgressSink`` implementation so that
the pipeline itself has no direct dependency on Telegram progress helpers.
When no sink is provided, a ``TelegramProgressSink`` is built from the job's
``telegram_context`` as the default.

**Current channel support**: only ``DeliveryChannel.TELEGRAM`` is implemented
end-to-end here.  Support for other delivery channels (e.g. ``WEB``) is
deferred to later feature slices (S2+) and will be wired in separately once
channel-specific presenter and delivery adapters are available.

Dependencies can be injected for unit testing (adapter, analysis_service,
translation_service, http_client, raw_payload_repo, progress_sink).  When not
supplied, production defaults are used.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from src.adapters.registry import resolve_adapter
from src.analysis.context import AnalysisContext
from src.analysis.modules.ai_summary import AISummaryModule, AISummaryResult
from src.analysis.modules.reviews import AirbnbReviewsModule, GenericReviewsModule, ReviewsResult
from src.analysis.openrouter_client import OpenRouterError
from src.analysis.registry import ModuleRegistry
from src.analysis.result import ReviewInsightsBlock
from src.analysis.reviews.service import ReviewAnalysisService
from src.analysis.runner import ModuleRunner
from src.analysis.service import AnalysisService
from src.domain.delivery import ProgressSink
from src.domain.listing import AnalysisJob
from src.domain.raw_payload import RawPayload
from src.enrichment.runner import EnrichmentOutcome, EnrichmentProvider, run_enrichments
from src.i18n import get_string
from src.i18n.types import Language
from src.telegram.formatter import format_analysis_message
from src.telegram.progress import TelegramProgressSink
from src.telegram.sender import send_message
from src.translation.service import TranslationError, TranslationService

if TYPE_CHECKING:
    from src.adapters.base import ListingAdapter
    from src.app.config import Settings
    from src.storage.repository import RawPayloadRepository

logger = logging.getLogger(__name__)


class UnsupportedProviderError(Exception):
    """Raised when no adapter is registered for the job's listing provider."""


def _map_reviews_result(rv: ReviewsResult | None) -> ReviewInsightsBlock | None:
    """Map a ``ReviewsResult`` module output into a ``ReviewInsightsBlock``.

    Returns ``None`` when *rv* is ``None`` (no reviews module produced a
    result).  List fields typed as ``list[dict]`` in ``ReviewsResult`` have
    their ``"summary"`` key extracted; the same guard is applied to the
    ``list[str]`` fields so that unexpected dict payloads from the AI are
    handled safely.
    """
    if rv is None:
        return None

    def _extract(items: list) -> list[str]:
        result = []
        for item in items:
            text = item.get("summary", "") if isinstance(item, dict) else str(item)
            if text:
                result.append(text)
        return result

    return ReviewInsightsBlock(
        overall_assessment=rv.overall_assessment or "",
        overall_risk_level=rv.overall_risk_level or "",
        review_count=rv.review_count,
        average_rating=rv.average_rating,
        critical_red_flags=_extract(rv.critical_red_flags),
        recurring_issues=_extract(rv.recurring_issues),
        conflicts_or_disputes=_extract(rv.conflicts_or_disputes),
        positive_signals=_extract(rv.positive_signals),
        window_view_summary=rv.window_view_summary or "",
    )


async def process_job(
    job: AnalysisJob,
    settings: "Settings",
    *,
    adapter: "ListingAdapter | None" = None,
    analysis_service: AnalysisService | None = None,
    translation_service: TranslationService | None = None,
    http_client: httpx.AsyncClient | None = None,
    enrichment_providers: list[EnrichmentProvider] | None = None,
    raw_payload_repo: "RawPayloadRepository | None" = None,
    progress_sink: ProgressSink | None = None,
) -> None:
    """Process one queued analysis job end-to-end.

    Parameters
    ----------
    job:
        The dequeued ``AnalysisJob`` to process.
    settings:
        Application settings used to construct default service/client
        dependencies and to supply the Telegram bot token.
    adapter:
        Optional pre-built ``ListingAdapter``.  When ``None`` the adapter is
        resolved from the registry using the job's source URL.
    analysis_service:
        Optional pre-built ``AnalysisService``.  When ``None`` one is
        constructed from *settings*.
    translation_service:
        Optional pre-built ``TranslationService``.  When ``None`` one is
        constructed from *settings*.  For English jobs the service is never
        called regardless.
    http_client:
        Optional ``httpx.AsyncClient`` injected into ``send_message`` for
        testing without real network calls.
    enrichment_providers:
        Optional list of enrichment providers to run after the listing is
        fetched.  Failures are recorded but never propagate; an empty list
        or ``None`` skips enrichment entirely.
    raw_payload_repo:
        Optional repository for persisting the raw adapter response.  When
        provided, the raw payload is saved before the normalised listing
        proceeds through the analysis pipeline.  Save errors are logged and
        swallowed — they never block the analysis.
    progress_sink:
        Optional ``ProgressSink`` for reporting pipeline stage progress to the
        user.  When ``None`` a ``TelegramProgressSink`` is constructed from the
        job's ``telegram_context`` as the production default.

    Raises
    ------
    UnsupportedProviderError
        If no adapter is registered for the job's listing provider.
    Exception
        Propagates any exception from the adapter fetch, analysis service,
        translation service, or Telegram send so the caller (worker loop)
        can decide how to handle it (e.g. log and continue, or dead-letter
        the job).
    """
    token = settings.telegram_bot_token
    tg_ctx = job.telegram_context
    if tg_ctx is None:
        raise ValueError(
            f"Job {job.id} has no telegram_context; Telegram delivery requires one"
        )
    chat_id = tg_ctx.chat_id

    # --- 1. Resolve adapter --------------------------------------------------
    if adapter is None:
        adapter = resolve_adapter(job.source_url)
    if adapter is None:
        raise UnsupportedProviderError(
            f"No adapter registered for provider {job.provider!r} "
            f"(url={job.source_url!r})"
        )

    logger.info(
        "Processing job %s: provider=%s url=%s chat=%s",
        job.id,
        job.provider,
        job.source_url,
        chat_id,
    )

    # Build the default Telegram progress sink when none was injected.
    sink: ProgressSink = progress_sink or TelegramProgressSink(
        token,
        tg_ctx.chat_id,
        tg_ctx.progress_message_id,
        client=http_client,
    )

    await sink.start()

    _pipeline_succeeded = False
    try:
        # Stage 1: extracting -----------------------------------------------
        await sink.update(get_string("msg.progress.extracting", job.language))

        # --- 2. Fetch listing (raw + normalised) -----------------------------
        adapter_result = await adapter.fetch(job.source_url)
        listing = adapter_result.listing
        logger.debug("Fetched listing %s for job %s", listing.id, job.id)

        # --- 2a. Build raw payload object; persist if a repo was provided ----
        _raw_payload = RawPayload(
            provider=job.provider.value,
            source_url=job.source_url,
            source_id=listing.source_id or None,
            payload=adapter_result.raw,
        )
        if raw_payload_repo is not None:
            try:
                await raw_payload_repo.save(_raw_payload)
            except Exception:
                logger.warning(
                    "Failed to persist raw payload for job %s; continuing without capture",
                    job.id,
                    exc_info=True,
                )

        # Stage 2: checking area/infrastructure (before enrichments) --------
        await sink.update(get_string("msg.progress.enriching", job.language))

        # --- 2b. Enrich (optional, tolerant) ---------------------------------
        enrichment_outcome: EnrichmentOutcome | None = None
        if enrichment_providers:
            enrichment_outcome = await run_enrichments(listing, enrichment_providers)
            if enrichment_outcome.all_failed:
                logger.warning(
                    "All enrichments failed for listing %s (job %s); continuing without enrichment data",
                    listing.id,
                    job.id,
                )

        # Stage 3: analyzing reviews and listing details (before module runner)
        await sink.update(get_string("msg.progress.analysing", job.language))

        # --- 3. Analyse (via module framework) -------------------------------
        service = analysis_service or AnalysisService(settings)
        review_service = ReviewAnalysisService(settings)
        registry = ModuleRegistry()
        registry.register(AISummaryModule(service))
        registry.register(AirbnbReviewsModule(review_service))
        registry.register(GenericReviewsModule())
        runner = ModuleRunner(registry)
        ctx = AnalysisContext(
            listing=listing,
            enrichment=enrichment_outcome,
            raw_payload=_raw_payload,
        )
        module_results = await runner.run(ctx)
        ai_summary = next(
            (r for r in module_results if isinstance(r, AISummaryResult)), None
        )
        if ai_summary is None:
            raise RuntimeError(
                f"AISummaryModule produced no result for job {job.id}"
            )
        result = ai_summary.analysis_result

        # --- 3b. Map ReviewsResult into ReviewInsightsBlock ------------------
        reviews_module_result = next(
            (r for r in module_results if isinstance(r, ReviewsResult)), None
        )
        review_insights = _map_reviews_result(reviews_module_result)

        result = result.model_copy(update={"display_title": listing.title, "review_insights": review_insights})
        logger.debug("Analysis complete for job %s", job.id)

        # Stage 4: preparing final report (before translate/format/send) ----
        await sink.update(get_string("msg.progress.preparing", job.language))

        # --- 4. Translate (on demand, ephemeral) -----------------------------
        # English jobs use the canonical result directly.  For other languages the
        # freeform blocks are translated just-in-time; translated output is never
        # persisted as a cache artifact.
        t_service = translation_service or TranslationService(settings)
        render_language = job.language
        try:
            translated_result = await t_service.translate(result, job.language)
            logger.debug(
                "Translation stage complete for job %s (language=%s)",
                job.id,
                job.language.value,
            )
        except (TranslationError, OpenRouterError) as exc:
            logger.warning(
                "Translation failed for job %s (requested_language=%s); falling back to English: %s",
                job.id,
                job.language.value,
                exc,
            )
            translated_result = result
            render_language = Language.EN

        # --- 5. Format -------------------------------------------------------
        text = format_analysis_message(listing, translated_result, render_language)

        # --- 6. Send final result ---------------------------------------------
        await send_message(token, chat_id, text, client=http_client)
        logger.info("Reply sent for job %s to chat %s", job.id, chat_id)
        _pipeline_succeeded = True

    finally:
        # Notify the sink whether the pipeline completed successfully or not
        # so that channel-specific implementations can handle each case
        # differently (e.g. surface an error indicator on failure).
        if _pipeline_succeeded:
            await sink.complete()
        else:
            await sink.fail()
