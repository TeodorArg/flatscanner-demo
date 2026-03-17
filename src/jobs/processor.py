"""End-to-end analysis job processor.

``process_job`` is the single function that drives a queued ``AnalysisJob``
through the full pipeline:

1. Resolve the adapter for the job's listing provider.
2. Fetch and normalise the listing via the adapter.
3. Run AI analysis through ``AnalysisService``.
4. Format the result with ``format_analysis_message``.
5. Send the Telegram reply via ``send_message``.

Dependencies can be injected for unit testing (adapter, analysis_service,
http_client).  When not supplied, production defaults are used.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from src.adapters.registry import resolve_adapter
from src.analysis.service import AnalysisService
from src.domain.listing import AnalysisJob
from src.enrichment.runner import EnrichmentProvider, run_enrichments
from src.telegram.formatter import format_analysis_message
from src.telegram.sender import send_message

if TYPE_CHECKING:
    from src.adapters.base import ListingAdapter
    from src.app.config import Settings

logger = logging.getLogger(__name__)


class UnsupportedProviderError(Exception):
    """Raised when no adapter is registered for the job's listing provider."""


async def process_job(
    job: AnalysisJob,
    settings: "Settings",
    *,
    adapter: "ListingAdapter | None" = None,
    analysis_service: AnalysisService | None = None,
    http_client: httpx.AsyncClient | None = None,
    enrichment_providers: list[EnrichmentProvider] | None = None,
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
    http_client:
        Optional ``httpx.AsyncClient`` injected into ``send_message`` for
        testing without real network calls.
    enrichment_providers:
        Optional list of enrichment providers to run after the listing is
        fetched.  Failures are recorded but never propagate; an empty list
        or ``None`` skips enrichment entirely.

    Raises
    ------
    UnsupportedProviderError
        If no adapter is registered for the job's listing provider.
    Exception
        Propagates any exception from the adapter fetch, analysis service,
        or Telegram send so the caller (worker loop) can decide how to handle
        it (e.g. log and continue, or dead-letter the job).
    """
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
        job.telegram_chat_id,
    )

    # --- 2. Fetch listing ----------------------------------------------------
    listing = await adapter.fetch(job.source_url)
    logger.debug("Fetched listing %s for job %s", listing.id, job.id)

    # --- 2b. Enrich (optional, tolerant) -------------------------------------
    if enrichment_providers:
        enrichment_outcome = await run_enrichments(listing, enrichment_providers)
        if enrichment_outcome.all_failed:
            logger.warning(
                "All enrichments failed for listing %s (job %s); continuing without enrichment data",
                listing.id,
                job.id,
            )

    # --- 3. Analyse ----------------------------------------------------------
    service = analysis_service or AnalysisService(settings)
    result = await service.analyse(listing)
    logger.debug("Analysis complete for job %s", job.id)

    # --- 4. Format -----------------------------------------------------------
    text = format_analysis_message(listing, result)

    # --- 5. Send -------------------------------------------------------------
    await send_message(
        settings.telegram_bot_token,
        job.telegram_chat_id,
        text,
        client=http_client,
    )
    logger.info("Reply sent for job %s to chat %s", job.id, job.telegram_chat_id)
