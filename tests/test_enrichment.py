"""Orchestration tests for partial-enrichment scenarios.

These tests prove that the enrichment runner:
- Collects successful results and records failures separately
- Never raises — the pipeline continues even when every provider fails
- Handles timeouts gracefully (recorded as failures, not raised)
- Passes the listing through to each provider

They also prove that process_job continues normally when enrichment
providers are injected and all of them fail.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.analysis.result import AnalysisResult, PriceVerdict
from src.analysis.service import AnalysisService
from src.domain.delivery import DeliveryChannel, TelegramDeliveryContext
from src.domain.listing import (
    AnalysisJob,
    ListingProvider,
    NormalizedListing,
    PriceInfo,
)
from src.adapters.base import AdapterResult
from src.enrichment.runner import (
    EnrichmentOutcome,
    EnrichmentProvider,
    EnrichmentProviderResult,
    run_enrichments,
)
from src.jobs.processor import process_job


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_listing() -> NormalizedListing:
    return NormalizedListing(
        provider=ListingProvider.AIRBNB,
        source_url="https://www.airbnb.com/rooms/99999",
        source_id="99999",
        title="Test flat",
        price=PriceInfo(amount=Decimal("100"), currency="EUR"),
    )


def _make_adapter_result(listing: NormalizedListing | None = None) -> AdapterResult:
    if listing is None:
        listing = _make_listing()
    return AdapterResult(raw={"id": listing.source_id, "name": listing.title}, listing=listing)


def _make_job() -> AnalysisJob:
    return AnalysisJob(
        source_url="https://www.airbnb.com/rooms/99999",
        provider=ListingProvider.AIRBNB,
        delivery_channel=DeliveryChannel.TELEGRAM,
        telegram_context=TelegramDeliveryContext(chat_id=42, message_id=1),
    )


def _make_result() -> AnalysisResult:
    return AnalysisResult(
        summary="Fine place.",
        strengths=["Good location"],
        risks=[],
        price_verdict=PriceVerdict.FAIR,
        price_explanation="Reasonable.",
    )


def _make_settings(**overrides):
    from src.app.config import Settings

    defaults = dict(
        app_env="testing",
        telegram_bot_token="test-token",
        openrouter_api_key="test-key",
        apify_api_token="test-apify",
    )
    defaults.update(overrides)
    return Settings(**defaults)


def _make_passthrough_ts():
    """Return a mock TranslationService that returns the result unchanged."""
    from src.translation.service import TranslationService

    mock_ts = MagicMock(spec=TranslationService)
    mock_ts.translate = AsyncMock(side_effect=lambda result, lang: result)
    return mock_ts


class _SuccessProvider:
    """Stub provider that always returns fixed data."""

    def __init__(self, name: str, data: dict[str, Any]) -> None:
        self._name = name
        self._data = data

    @property
    def name(self) -> str:
        return self._name

    async def enrich(self, listing: NormalizedListing) -> dict[str, Any]:
        return self._data


class _FailingProvider:
    """Stub provider that always raises."""

    def __init__(self, name: str, exc: Exception | None = None) -> None:
        self._name = name
        self._exc = exc or RuntimeError(f"{name} failed")

    @property
    def name(self) -> str:
        return self._name

    async def enrich(self, listing: NormalizedListing) -> dict[str, Any]:
        raise self._exc


class _SlowProvider:
    """Stub provider that never completes (simulates timeout)."""

    def __init__(self, name: str, delay: float = 999.0) -> None:
        self._name = name
        self._delay = delay

    @property
    def name(self) -> str:
        return self._name

    async def enrich(self, listing: NormalizedListing) -> dict[str, Any]:
        await asyncio.sleep(self._delay)
        return {}  # pragma: no cover


# ---------------------------------------------------------------------------
# run_enrichments — no providers
# ---------------------------------------------------------------------------


class TestRunEnrichmentsEmpty:
    @pytest.mark.asyncio
    async def test_returns_empty_outcome_for_no_providers(self):
        listing = _make_listing()
        outcome = await run_enrichments(listing, [])

        assert isinstance(outcome, EnrichmentOutcome)
        assert outcome.successes == []
        assert outcome.failures == []
        assert not outcome.all_failed

    @pytest.mark.asyncio
    async def test_empty_outcome_all_failed_is_false(self):
        """all_failed requires at least one failure; empty is not a failure."""
        listing = _make_listing()
        outcome = await run_enrichments(listing, [])
        assert outcome.all_failed is False


# ---------------------------------------------------------------------------
# run_enrichments — all succeed
# ---------------------------------------------------------------------------


class TestRunEnrichmentsAllSucceed:
    @pytest.mark.asyncio
    async def test_all_results_in_successes(self):
        listing = _make_listing()
        providers = [
            _SuccessProvider("transit", {"score": 9}),
            _SuccessProvider("safety", {"index": 7}),
        ]
        outcome = await run_enrichments(listing, providers)

        assert len(outcome.successes) == 2
        assert outcome.failures == []

    @pytest.mark.asyncio
    async def test_success_data_is_preserved(self):
        listing = _make_listing()
        providers = [_SuccessProvider("transit", {"lines": 3})]
        outcome = await run_enrichments(listing, providers)

        assert outcome.successes[0].name == "transit"
        assert outcome.successes[0].data == {"lines": 3}
        assert outcome.successes[0].succeeded is True
        assert outcome.successes[0].error is None

    @pytest.mark.asyncio
    async def test_all_failed_is_false_when_all_succeed(self):
        listing = _make_listing()
        outcome = await run_enrichments(
            listing, [_SuccessProvider("x", {}), _SuccessProvider("y", {})]
        )
        assert outcome.all_failed is False


# ---------------------------------------------------------------------------
# run_enrichments — all fail
# ---------------------------------------------------------------------------


class TestRunEnrichmentsAllFail:
    @pytest.mark.asyncio
    async def test_does_not_raise_when_all_fail(self):
        listing = _make_listing()
        providers = [
            _FailingProvider("transit"),
            _FailingProvider("safety"),
        ]
        # Must not raise
        outcome = await run_enrichments(listing, providers)

        assert isinstance(outcome, EnrichmentOutcome)

    @pytest.mark.asyncio
    async def test_failures_recorded_correctly(self):
        listing = _make_listing()
        exc = ValueError("external api down")
        providers = [_FailingProvider("transit", exc)]

        outcome = await run_enrichments(listing, providers)

        assert outcome.successes == []
        assert len(outcome.failures) == 1
        result = outcome.failures[0]
        assert result.name == "transit"
        assert result.error is exc
        assert result.succeeded is False
        assert result.data is None

    @pytest.mark.asyncio
    async def test_all_failed_is_true_when_all_fail(self):
        listing = _make_listing()
        providers = [_FailingProvider("a"), _FailingProvider("b")]
        outcome = await run_enrichments(listing, providers)
        assert outcome.all_failed is True

    @pytest.mark.asyncio
    async def test_returns_outcome_not_raises_on_runtime_error(self):
        listing = _make_listing()
        outcome = await run_enrichments(
            listing, [_FailingProvider("x", RuntimeError("boom"))]
        )
        assert outcome.failures[0].error.__class__ is RuntimeError


# ---------------------------------------------------------------------------
# run_enrichments — mixed success / failure
# ---------------------------------------------------------------------------


class TestRunEnrichmentsMixed:
    @pytest.mark.asyncio
    async def test_mixed_success_and_failure(self):
        listing = _make_listing()
        providers = [
            _SuccessProvider("transit", {"score": 8}),
            _FailingProvider("safety"),
            _SuccessProvider("places", {"count": 12}),
        ]
        outcome = await run_enrichments(listing, providers)

        assert len(outcome.successes) == 2
        assert len(outcome.failures) == 1

    @pytest.mark.asyncio
    async def test_success_names_are_correct(self):
        listing = _make_listing()
        providers = [
            _SuccessProvider("transit", {"x": 1}),
            _FailingProvider("safety"),
        ]
        outcome = await run_enrichments(listing, providers)

        success_names = {r.name for r in outcome.successes}
        failure_names = {r.name for r in outcome.failures}
        assert success_names == {"transit"}
        assert failure_names == {"safety"}

    @pytest.mark.asyncio
    async def test_all_failed_is_false_when_some_succeed(self):
        listing = _make_listing()
        providers = [
            _SuccessProvider("transit", {}),
            _FailingProvider("safety"),
        ]
        outcome = await run_enrichments(listing, providers)
        assert outcome.all_failed is False


# ---------------------------------------------------------------------------
# run_enrichments — timeout tolerance
# ---------------------------------------------------------------------------


class TestRunEnrichmentsTimeout:
    @pytest.mark.asyncio
    async def test_timed_out_provider_recorded_as_failure(self):
        listing = _make_listing()
        # Use a very short timeout so the test completes quickly
        providers = [_SlowProvider("slow_api", delay=999.0)]

        outcome = await run_enrichments(listing, providers, timeout=0.01)

        assert len(outcome.failures) == 1
        assert outcome.failures[0].name == "slow_api"
        assert isinstance(outcome.failures[0].error, asyncio.TimeoutError)

    @pytest.mark.asyncio
    async def test_timeout_does_not_block_other_providers(self):
        """A timed-out provider must not prevent fast providers from completing."""
        listing = _make_listing()
        providers = [
            _SlowProvider("slow", delay=999.0),
            _SuccessProvider("fast", {"ok": True}),
        ]

        outcome = await run_enrichments(listing, providers, timeout=0.05)

        success_names = {r.name for r in outcome.successes}
        failure_names = {r.name for r in outcome.failures}
        assert "fast" in success_names
        assert "slow" in failure_names

    @pytest.mark.asyncio
    async def test_all_timeout_pipeline_continues(self):
        """Even when all providers time out, run_enrichments returns an outcome."""
        listing = _make_listing()
        providers = [
            _SlowProvider("a", delay=999.0),
            _SlowProvider("b", delay=999.0),
        ]
        outcome = await run_enrichments(listing, providers, timeout=0.01)

        assert outcome.all_failed is True
        assert len(outcome.failures) == 2

    @pytest.mark.asyncio
    async def test_provider_receives_listing(self):
        """The listing passed to run_enrichments is forwarded to providers."""
        listing = _make_listing()
        received: list[NormalizedListing] = []

        class _CapturingProvider:
            name = "capture"

            async def enrich(self, lst: NormalizedListing) -> dict[str, Any]:
                received.append(lst)
                return {}

        await run_enrichments(listing, [_CapturingProvider()])

        assert received == [listing]


# ---------------------------------------------------------------------------
# process_job integration — enrichment is called and tolerates failures
# ---------------------------------------------------------------------------


class TestProcessJobEnrichmentIntegration:
    @pytest.mark.asyncio
    async def test_process_job_continues_when_all_enrichments_fail(self):
        """pipeline completes normally even when all enrichment providers fail."""
        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        providers = [_FailingProvider("transit"), _FailingProvider("safety")]

        with patch("src.telegram.presenter.send_message", new_callable=AsyncMock):
            # Must not raise
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
                enrichment_providers=providers,
            )

        mock_service.analyse.assert_awaited_once()
        assert mock_service.analyse.call_args.args[0] is listing
        forwarded_outcome = mock_service.analyse.call_args.args[1]
        assert isinstance(forwarded_outcome, EnrichmentOutcome)
        assert forwarded_outcome.successes == []
        assert len(forwarded_outcome.failures) == 2

    @pytest.mark.asyncio
    async def test_process_job_continues_when_enrichments_time_out(self):
        """Timed-out enrichments do not block the pipeline."""
        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        providers = [_SlowProvider("slow", delay=999.0)]

        async def fast_enrich(lst, provs, **_kw):
            return await run_enrichments(lst, provs, timeout=0.01)

        with (
            patch("src.telegram.presenter.send_message", new_callable=AsyncMock),
            patch("src.jobs.processor.run_enrichments", side_effect=fast_enrich),
        ):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
                enrichment_providers=providers,
            )

        mock_service.analyse.assert_awaited_once()
        assert mock_service.analyse.call_args.args[0] is listing
        forwarded_outcome = mock_service.analyse.call_args.args[1]
        assert isinstance(forwarded_outcome, EnrichmentOutcome)
        assert forwarded_outcome.successes == []
        assert len(forwarded_outcome.failures) == 1
        assert isinstance(forwarded_outcome.failures[0].error, asyncio.TimeoutError)

    @pytest.mark.asyncio
    async def test_process_job_calls_run_enrichments_with_providers(self):
        """run_enrichments is called with the fetched listing and providers."""
        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        providers = [_SuccessProvider("transit", {"score": 5})]
        calls: list[tuple] = []

        async def capture_enrich(lst, provs, **kw):
            calls.append((lst, provs))
            return EnrichmentOutcome()

        with (
            patch("src.jobs.processor.run_enrichments", side_effect=capture_enrich),
            patch("src.telegram.presenter.send_message", new_callable=AsyncMock),
        ):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
                enrichment_providers=providers,
            )

        assert len(calls) == 1
        assert calls[0][0] is listing
        assert calls[0][1] is providers

    @pytest.mark.asyncio
    async def test_process_job_skips_enrichment_when_no_providers(self):
        """run_enrichments is NOT called when enrichment_providers is None."""
        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        with (
            patch(
                "src.jobs.processor.run_enrichments", new_callable=AsyncMock
            ) as mock_run,
            patch("src.telegram.presenter.send_message", new_callable=AsyncMock),
        ):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
                # no enrichment_providers
            )

        mock_run.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_job_succeeds_with_mixed_enrichment_outcome(self):
        """Pipeline succeeds when some enrichments pass and some fail."""
        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        providers = [
            _SuccessProvider("transit", {"score": 8}),
            _FailingProvider("safety"),
        ]

        sent_texts: list[str] = []

        async def fake_send(token, chat_id, text, *, parse_mode=None, client=None):
            sent_texts.append(text)

        with patch("src.telegram.presenter.send_message", side_effect=fake_send):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
                enrichment_providers=providers,
            )

        assert len(sent_texts) == 1
        assert "Test flat" in sent_texts[0]

