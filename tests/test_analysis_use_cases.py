"""Tests for the S2 shared application use-case layer.

Covers:
- submit_analysis_request delegates to enqueue_analysis_job.
- run_analysis_job delegates to process_job with all injected dependencies.
- The router calls submit_analysis_request (not enqueue_analysis_job directly).
- The worker calls run_analysis_job (not process_job directly).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.application.analysis import run_analysis_job, submit_analysis_request
from src.domain.delivery import DeliveryChannel, TelegramDeliveryContext
from src.domain.listing import AnalysisJob, ListingProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_job(**overrides) -> AnalysisJob:
    defaults = dict(
        source_url="https://www.airbnb.com/rooms/99999",
        provider=ListingProvider.AIRBNB,
        delivery_channel=DeliveryChannel.TELEGRAM,
        telegram_context=TelegramDeliveryContext(chat_id=42, message_id=1),
    )
    defaults.update(overrides)
    return AnalysisJob(**defaults)


# ---------------------------------------------------------------------------
# submit_analysis_request
# ---------------------------------------------------------------------------


class TestSubmitAnalysisRequest:
    @pytest.mark.asyncio
    async def test_delegates_to_enqueue_analysis_job(self):
        """submit_analysis_request must call enqueue_analysis_job and return its result."""
        job = _make_job()
        mock_redis = AsyncMock()

        # Patch at the source module because the import is deferred inside the function.
        with patch(
            "src.jobs.queue.enqueue_analysis_job",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_enqueue:
            result = await submit_analysis_request(mock_redis, job)

        mock_enqueue.assert_awaited_once_with(mock_redis, job)
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_on_duplicate(self):
        """submit_analysis_request returns False when enqueue_analysis_job says duplicate."""
        job = _make_job()
        mock_redis = AsyncMock()

        with patch(
            "src.jobs.queue.enqueue_analysis_job",
            new_callable=AsyncMock,
            return_value=False,
        ) as mock_enqueue:
            result = await submit_analysis_request(mock_redis, job)

        mock_enqueue.assert_awaited_once_with(mock_redis, job)
        assert result is False

    @pytest.mark.asyncio
    async def test_propagates_redis_errors(self):
        """submit_analysis_request does not swallow errors from enqueue_analysis_job."""
        from redis.asyncio import RedisError

        job = _make_job()
        mock_redis = AsyncMock()

        with patch(
            "src.jobs.queue.enqueue_analysis_job",
            new_callable=AsyncMock,
            side_effect=RedisError("boom"),
        ):
            with pytest.raises(RedisError):
                await submit_analysis_request(mock_redis, job)


# ---------------------------------------------------------------------------
# run_analysis_job
# ---------------------------------------------------------------------------


class TestRunAnalysisJob:
    @pytest.mark.asyncio
    async def test_delegates_to_process_job(self):
        """run_analysis_job must forward the job and settings to process_job."""
        job = _make_job()
        mock_settings = object()

        # Patch at the source module because the import is deferred inside the function.
        with patch(
            "src.jobs.processor.process_job",
            new_callable=AsyncMock,
        ) as mock_process:
            await run_analysis_job(job, mock_settings)

        mock_process.assert_awaited_once_with(
            job,
            mock_settings,
            adapter=None,
            analysis_service=None,
            translation_service=None,
            http_client=None,
            enrichment_providers=None,
            raw_payload_repo=None,
            progress_sink=None,
            result_presenter=None,
        )

    @pytest.mark.asyncio
    async def test_forwards_injected_dependencies(self):
        """run_analysis_job must pass optional injected deps through to process_job."""
        job = _make_job()
        mock_settings = object()
        mock_sink = AsyncMock()
        mock_http = AsyncMock()
        mock_presenter = object()

        with patch(
            "src.jobs.processor.process_job",
            new_callable=AsyncMock,
        ) as mock_process:
            await run_analysis_job(
                job,
                mock_settings,
                http_client=mock_http,
                progress_sink=mock_sink,
                result_presenter=mock_presenter,
            )

        _, call_kwargs = mock_process.call_args
        assert call_kwargs["http_client"] is mock_http
        assert call_kwargs["progress_sink"] is mock_sink
        assert call_kwargs["result_presenter"] is mock_presenter

    @pytest.mark.asyncio
    async def test_propagates_exceptions(self):
        """run_analysis_job must not swallow exceptions from process_job."""
        job = _make_job()

        with patch(
            "src.jobs.processor.process_job",
            new_callable=AsyncMock,
            side_effect=RuntimeError("pipeline failed"),
        ):
            with pytest.raises(RuntimeError, match="pipeline failed"):
                await run_analysis_job(job, object())


# ---------------------------------------------------------------------------
# Router integration: submit_analysis_request is the submission path
# ---------------------------------------------------------------------------


class TestRouterUsesSubmitAnalysisRequest:
    """Verify that the Telegram router goes through the use-case layer."""

    def test_router_imports_submit_analysis_request(self):
        """src.telegram.router must import submit_analysis_request from the use-case layer."""
        import src.telegram.router as router_mod

        assert hasattr(router_mod, "submit_analysis_request"), (
            "router module must expose submit_analysis_request via import"
        )

    def test_router_does_not_import_enqueue_analysis_job(self):
        """src.telegram.router must not import enqueue_analysis_job directly."""
        import importlib
        import sys

        mod = sys.modules.get("src.telegram.router")
        if mod is None:
            mod = importlib.import_module("src.telegram.router")

        assert not hasattr(mod, "enqueue_analysis_job"), (
            "router module must not expose enqueue_analysis_job directly; "
            "use submit_analysis_request from the application layer instead"
        )


# ---------------------------------------------------------------------------
# Worker integration: run_analysis_job is the execution path
# ---------------------------------------------------------------------------


class TestWorkerUsesRunAnalysisJob:
    """Verify that the worker goes through the use-case layer."""

    def test_worker_imports_run_analysis_job(self):
        """src.jobs.worker must import run_analysis_job from the use-case layer."""
        import src.jobs.worker as worker_mod

        assert hasattr(worker_mod, "run_analysis_job"), (
            "worker module must expose run_analysis_job via import"
        )

    def test_worker_does_not_import_process_job(self):
        """src.jobs.worker must not import process_job directly."""
        import importlib
        import sys

        mod = sys.modules.get("src.jobs.worker")
        if mod is None:
            mod = importlib.import_module("src.jobs.worker")

        assert not hasattr(mod, "process_job"), (
            "worker module must not expose process_job directly; "
            "use run_analysis_job from the application layer instead"
        )
