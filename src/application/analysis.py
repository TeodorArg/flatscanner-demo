"""Shared application use-cases for analysis submission and execution.

These two functions are the canonical entry points for:

- Submitting an analysis request from any delivery channel
  (``submit_analysis_request``).
- Executing a dequeued analysis job through the full pipeline
  (``run_analysis_job``).

Both Telegram and future Web callers must go through this layer rather than
calling the queue and processor modules directly.  The layer is intentionally
thin for S2; it will grow as channel-specific presenter and result-delivery
adapters are introduced in later slices.

Imports from ``src.jobs`` are deferred to call time to avoid the circular
import that would result from the module-level import chain:
``application.analysis`` → ``jobs.processor`` → ``analysis`` (package) →
``app.config`` → ``app.main`` → ``telegram.router`` → ``application.analysis``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from src.domain.delivery import AnalysisResultPresenter, ProgressSink
from src.domain.listing import AnalysisJob
from src.enrichment.runner import EnrichmentProvider

if TYPE_CHECKING:
    from redis.asyncio import Redis

    from src.adapters.base import ListingAdapter
    from src.analysis.service import AnalysisService
    from src.app.config import Settings
    from src.storage.repository import RawPayloadRepository
    from src.translation.service import TranslationService


async def submit_analysis_request(redis: "Redis", job: AnalysisJob) -> bool:
    """Enqueue an analysis job for asynchronous processing.

    This is the single shared entry point for submitting an analysis request
    regardless of the originating delivery channel.  The caller is responsible
    for constructing the ``AnalysisJob`` with the correct channel context before
    calling this function.

    Parameters
    ----------
    redis:
        Async Redis client connected to the job queue.
    job:
        Fully constructed ``AnalysisJob`` ready to be enqueued.

    Returns
    -------
    bool
        ``True`` if the job was enqueued; ``False`` if a duplicate was detected
        and the job was skipped.
    """
    from src.jobs.queue import enqueue_analysis_job

    return await enqueue_analysis_job(redis, job)


async def run_analysis_job(
    job: AnalysisJob,
    settings: "Settings",
    *,
    adapter: "ListingAdapter | None" = None,
    analysis_service: "AnalysisService | None" = None,
    translation_service: "TranslationService | None" = None,
    http_client: httpx.AsyncClient | None = None,
    enrichment_providers: list[EnrichmentProvider] | None = None,
    raw_payload_repo: "RawPayloadRepository | None" = None,
    progress_sink: ProgressSink | None = None,
    result_presenter: AnalysisResultPresenter | None = None,
) -> None:
    """Execute an analysis job through the full pipeline.

    This is the single shared entry point for running a dequeued job.  The
    worker calls this function instead of the lower-level ``process_job``
    directly so that the application layer remains the stable API boundary.

    All parameters are forwarded to ``process_job``; see its docstring for
    full parameter documentation.  Dependencies can be injected for testing.
    """
    from src.jobs.processor import process_job

    await process_job(
        job,
        settings,
        adapter=adapter,
        analysis_service=analysis_service,
        translation_service=translation_service,
        http_client=http_client,
        enrichment_providers=enrichment_providers,
        raw_payload_repo=raw_payload_repo,
        progress_sink=progress_sink,
        result_presenter=result_presenter,
    )
