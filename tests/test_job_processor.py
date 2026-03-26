"""Tests for the end-to-end job processor, dequeue helper, and worker loop."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.adapters.apify_client import ApifyError
from src.adapters.base import AdapterResult
from src.analysis.openrouter_client import OpenRouterError
from src.analysis.result import AnalysisResult, PriceVerdict
from src.analysis.service import AnalysisService
from src.domain.delivery import DeliveryChannel, TelegramDeliveryContext
from src.domain.listing import (
    AnalysisJob,
    JobStatus,
    ListingProvider,
    NormalizedListing,
    PriceInfo,
)
from src.i18n.types import Language
from src.jobs.processor import UnsupportedProviderError, process_job
from src.jobs.queue import QUEUE_KEY, dequeue_analysis_job
from src.jobs.worker import process_once, run_worker
from src.translation.service import TranslationError


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_job(**overrides) -> AnalysisJob:
    defaults = dict(
        source_url="https://www.airbnb.com/rooms/12345",
        provider=ListingProvider.AIRBNB,
        delivery_channel=DeliveryChannel.TELEGRAM,
        telegram_context=TelegramDeliveryContext(chat_id=1001, message_id=7),
    )
    defaults.update(overrides)
    return AnalysisJob(**defaults)


def _make_listing() -> NormalizedListing:
    return NormalizedListing(
        provider=ListingProvider.AIRBNB,
        source_url="https://www.airbnb.com/rooms/12345",
        source_id="12345",
        title="Cozy flat in Berlin",
        price=PriceInfo(amount=Decimal("80"), currency="EUR"),
    )


def _make_adapter_result(listing: NormalizedListing | None = None) -> AdapterResult:
    """Return an ``AdapterResult`` wrapping *listing* (or a default listing)."""
    if listing is None:
        listing = _make_listing()
    return AdapterResult(raw={"id": listing.source_id, "name": listing.title}, listing=listing)


def _make_result() -> AnalysisResult:
    return AnalysisResult(
        display_title="Cozy flat in Berlin",
        summary="A pleasant flat in central Berlin.",
        strengths=["Central location", "Modern kitchen"],
        risks=["Noisy street"],
        price_verdict=PriceVerdict.FAIR,
        price_explanation="Price is in line with comparable listings.",
    )


def _make_settings(**overrides):
    from src.app.config import Settings

    defaults = dict(
        app_env="testing",
        telegram_bot_token="test-bot-token",
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


# ---------------------------------------------------------------------------
# process_job — success path
# ---------------------------------------------------------------------------


class TestProcessJobSuccess:
    @pytest.mark.asyncio
    async def test_sends_formatted_message_to_correct_chat(self):
        """Full happy-path: adapter fetch → analysis → formatted Telegram reply."""
        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        sent_texts: list[str] = []
        sent_chats: list[int] = []

        async def fake_send(token, chat_id, text, *, client=None):
            sent_texts.append(text)
            sent_chats.append(chat_id)

        with patch("src.telegram.presenter.send_message", side_effect=fake_send):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
            )

        assert sent_chats == [job.telegram_context.chat_id]
        assert "Cozy flat in Berlin" in sent_texts[0]
        assert "A pleasant flat in central Berlin." in sent_texts[0]

    @pytest.mark.asyncio
    async def test_adapter_fetch_called_with_job_source_url(self):
        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        with patch("src.telegram.presenter.send_message", new_callable=AsyncMock):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
            )

        mock_adapter.fetch.assert_awaited_once_with(job.source_url)

    @pytest.mark.asyncio
    async def test_analysis_service_called_with_fetched_listing(self):
        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        with patch("src.telegram.presenter.send_message", new_callable=AsyncMock):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
            )

        mock_service.analyse.assert_awaited_once()
        assert mock_service.analyse.call_args.args[0] is listing

    @pytest.mark.asyncio
    async def test_send_message_uses_bot_token_from_settings(self):
        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings(telegram_bot_token="my-secret-token")

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        captured_tokens: list[str] = []

        async def capture_send(token, chat_id, text, *, client=None):
            captured_tokens.append(token)

        with patch("src.telegram.presenter.send_message", side_effect=capture_send):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
            )

        assert captured_tokens == ["my-secret-token"]

    @pytest.mark.asyncio
    async def test_resolve_adapter_used_when_none_injected(self):
        """When no adapter is passed, resolve_adapter is called with the job URL."""
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
                "src.jobs.processor.resolve_adapter", return_value=mock_adapter
            ) as mock_resolve,
            patch("src.telegram.presenter.send_message", new_callable=AsyncMock),
        ):
            await process_job(
                job, settings, analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
            )

        mock_resolve.assert_called_once_with(job.source_url)

    @pytest.mark.asyncio
    async def test_injected_result_presenter_receives_translated_result(self):
        """When result_presenter is injected, processor delegates final delivery to it."""
        job = _make_job(language=Language.ES)
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        translated_result = result.model_copy(
            update={"display_title": "Apartamento acogedor en Berlin"}
        )
        mock_translation_service = MagicMock()
        mock_translation_service.translate = AsyncMock(return_value=translated_result)
        mock_presenter = MagicMock()
        mock_presenter.deliver = AsyncMock()

        await process_job(
            job,
            settings,
            adapter=mock_adapter,
            analysis_service=mock_service,
            translation_service=mock_translation_service,
            result_presenter=mock_presenter,
        )

        mock_presenter.deliver.assert_awaited_once_with(
            listing,
            translated_result,
            Language.ES,
        )


# ---------------------------------------------------------------------------
# process_job — failure paths
# ---------------------------------------------------------------------------


class TestProcessJobUnsupportedProvider:
    @pytest.mark.asyncio
    async def test_raises_when_no_adapter_in_registry(self):
        """UnsupportedProviderError raised when resolve_adapter returns None."""
        job = _make_job(
            source_url="https://www.booking.com/hotel/xyz",
            provider=ListingProvider.UNKNOWN,
        )
        settings = _make_settings()

        with patch("src.jobs.processor.resolve_adapter", return_value=None):
            with pytest.raises(UnsupportedProviderError):
                await process_job(job, settings)

    @pytest.mark.asyncio
    async def test_error_message_contains_provider_and_url(self):
        job = _make_job(
            source_url="https://www.booking.com/hotel/xyz",
            provider=ListingProvider.UNKNOWN,
        )
        settings = _make_settings()

        with patch("src.jobs.processor.resolve_adapter", return_value=None):
            with pytest.raises(UnsupportedProviderError) as exc_info:
                await process_job(job, settings)

        msg = str(exc_info.value)
        assert "booking.com" in msg or "unknown" in msg.lower()


class TestProcessJobAdapterFailure:
    @pytest.mark.asyncio
    async def test_propagates_adapter_value_error(self):
        """Empty dataset from adapter (listing not found) propagates as ValueError."""
        job = _make_job()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(
            side_effect=ValueError("Apify returned empty dataset")
        )

        with pytest.raises(ValueError, match="empty dataset"):
            await process_job(job, settings, adapter=mock_adapter)

    @pytest.mark.asyncio
    async def test_propagates_adapter_apify_error(self):
        from src.adapters.apify_client import ApifyError

        job = _make_job()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(
            side_effect=ApifyError("Actor run failed with status FAILED")
        )

        with pytest.raises(ApifyError):
            await process_job(job, settings, adapter=mock_adapter)


class TestProcessJobAnalysisFailure:
    @pytest.mark.asyncio
    async def test_propagates_openrouter_error(self):
        job = _make_job()
        listing = _make_listing()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(
            side_effect=OpenRouterError("OpenRouter request failed with status 500")
        )

        with pytest.raises(OpenRouterError):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
            )

    @pytest.mark.asyncio
    async def test_propagates_value_error_from_bad_model_response(self):
        job = _make_job()
        listing = _make_listing()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(
            side_effect=ValueError("Model response is not valid JSON")
        )

        with pytest.raises(ValueError, match="not valid JSON"):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
            )


class TestProcessJobSendFailure:
    @pytest.mark.asyncio
    async def test_propagates_httpx_error_on_send_failure(self):
        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        async def failing_send(token, chat_id, text, *, client=None):
            raise httpx.HTTPStatusError(
                "403 Forbidden",
                request=MagicMock(),
                response=MagicMock(status_code=403),
            )

        with (
            patch("src.telegram.presenter.send_message", side_effect=failing_send),
            pytest.raises(httpx.HTTPStatusError),
        ):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
            )


class TestProcessJobTranslationFallback:
    @pytest.mark.asyncio
    async def test_translation_error_falls_back_to_english_reply(self):
        job = _make_job(language=Language.RU)
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        mock_translation_service = MagicMock()
        mock_translation_service.translate = AsyncMock(
            side_effect=TranslationError("model returned invalid JSON")
        )

        sent_texts: list[str] = []

        async def fake_send(token, chat_id, text, *, client=None):
            sent_texts.append(text)

        with patch("src.telegram.presenter.send_message", side_effect=fake_send):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=mock_translation_service,
            )

        assert sent_texts
        assert "A pleasant flat in central Berlin." in sent_texts[0]
        assert "Price:" in sent_texts[0]


class TestProcessJobLocalizedTitle:
    @pytest.mark.asyncio
    async def test_uses_translated_display_title_in_sent_message(self):
        job = _make_job(language=Language.ES)
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        translated_result = result.model_copy(
            update={"display_title": "Apartamento acogedor en Berlin"}
        )
        mock_translation_service = MagicMock()
        mock_translation_service.translate = AsyncMock(return_value=translated_result)

        sent_texts: list[str] = []

        async def fake_send(token, chat_id, text, *, client=None):
            sent_texts.append(text)

        with patch("src.telegram.presenter.send_message", side_effect=fake_send):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=mock_translation_service,
            )

        assert sent_texts
        assert sent_texts[0].startswith("Apartamento acogedor en Berlin")


# ---------------------------------------------------------------------------
# dequeue_analysis_job
# ---------------------------------------------------------------------------


class TestDequeueAnalysisJob:
    @pytest.mark.asyncio
    async def test_returns_none_when_brpop_times_out(self):
        redis = AsyncMock()
        redis.brpop.return_value = None
        result = await dequeue_analysis_job(redis, timeout=1)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_analysis_job_from_payload(self):
        job = _make_job()
        payload = job.model_dump_json()
        redis = AsyncMock()
        redis.brpop.return_value = (QUEUE_KEY, payload)

        dequeued = await dequeue_analysis_job(redis, timeout=1)
        assert dequeued is not None
        assert dequeued.id == job.id
        assert dequeued.source_url == job.source_url
        assert dequeued.telegram_context.chat_id == job.telegram_context.chat_id

    @pytest.mark.asyncio
    async def test_brpop_called_with_queue_key_and_timeout(self):
        redis = AsyncMock()
        redis.brpop.return_value = None
        await dequeue_analysis_job(redis, timeout=5)
        redis.brpop.assert_awaited_once_with(QUEUE_KEY, timeout=5)

    @pytest.mark.asyncio
    async def test_default_timeout_is_zero(self):
        redis = AsyncMock()
        redis.brpop.return_value = None
        await dequeue_analysis_job(redis)
        # timeout may be positional or keyword
        call_kwargs = redis.brpop.call_args[1]
        call_args = redis.brpop.call_args[0]
        timeout_val = call_kwargs.get("timeout", call_args[1] if len(call_args) > 1 else None)
        assert timeout_val == 0


# ---------------------------------------------------------------------------
# process_once
# ---------------------------------------------------------------------------


class TestProcessOnce:
    @pytest.mark.asyncio
    async def test_returns_false_when_queue_empty(self):
        redis = AsyncMock()
        redis.brpop.return_value = None
        settings = _make_settings()
        result = await process_once(redis, settings)
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_and_processes_job(self):
        job = _make_job()
        listing = _make_listing()
        result_obj = _make_result()
        settings = _make_settings()

        redis = AsyncMock()
        redis.brpop.return_value = (QUEUE_KEY, job.model_dump_json())

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result_obj)

        with (
            patch("src.jobs.processor.resolve_adapter", return_value=mock_adapter),
            patch("src.jobs.processor.AnalysisService", return_value=mock_service),
            patch("src.jobs.processor.TranslationService", return_value=_make_passthrough_ts()),
            patch("src.telegram.presenter.send_message", new_callable=AsyncMock),
        ):
            outcome = await process_once(redis, settings)

        assert outcome is True

    @pytest.mark.asyncio
    async def test_propagates_processing_errors(self):
        """process_once does not swallow errors — that is the worker loop's job."""
        job = _make_job()
        settings = _make_settings()

        redis = AsyncMock()
        redis.brpop.return_value = (QUEUE_KEY, job.model_dump_json())

        with patch(
            "src.jobs.processor.resolve_adapter",
            return_value=None,  # will raise UnsupportedProviderError
        ):
            with pytest.raises(UnsupportedProviderError):
                await process_once(redis, settings)


# ---------------------------------------------------------------------------
# run_worker
# ---------------------------------------------------------------------------


class TestRunWorker:
    @pytest.mark.asyncio
    async def test_exits_cleanly_on_cancelled_error(self):
        """run_worker must stop without raising when cancelled."""
        settings = _make_settings()
        redis = AsyncMock()

        async def brpop_raise_cancelled(*args, **kwargs):
            raise asyncio.CancelledError

        redis.brpop.side_effect = brpop_raise_cancelled

        # Should not raise
        await run_worker(redis, settings)

        redis.brpop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_continues_after_unsupported_provider_error(self):
        """UnsupportedProviderError is logged and the loop continues."""
        settings = _make_settings()
        redis = AsyncMock()
        job = _make_job()

        brpop_responses = iter([(QUEUE_KEY, job.model_dump_json())])

        async def brpop_side_effect(*args, **kwargs):
            try:
                return next(brpop_responses)
            except StopIteration:
                raise asyncio.CancelledError

        redis.brpop.side_effect = brpop_side_effect

        with patch(
            "src.jobs.worker.run_analysis_job",
            side_effect=UnsupportedProviderError("unknown provider"),
        ):
            await run_worker(redis, settings)

        assert redis.brpop.await_count == 2

    @pytest.mark.asyncio
    async def test_continues_after_generic_exception(self):
        """Generic processing errors are logged and the loop continues."""
        settings = _make_settings()
        redis = AsyncMock()
        job = _make_job()

        brpop_responses = iter([(QUEUE_KEY, job.model_dump_json())])

        async def brpop_side_effect(*args, **kwargs):
            try:
                return next(brpop_responses)
            except StopIteration:
                raise asyncio.CancelledError

        redis.brpop.side_effect = brpop_side_effect

        with (
            patch(
                "src.jobs.worker.run_analysis_job",
                side_effect=RuntimeError("transient network error"),
            ),
            patch(
                "src.jobs.worker.requeue_raw_payload", new_callable=AsyncMock
            ),
        ):
            await run_worker(redis, settings)

        assert redis.brpop.await_count == 2

    @pytest.mark.asyncio
    async def test_requeues_raw_payload_on_generic_exception(self):
        """A failed job is requeued instead of silently lost."""
        settings = _make_settings()
        redis = AsyncMock()
        job = _make_job()
        raw_payload = job.model_dump_json()

        brpop_responses = iter([(QUEUE_KEY, raw_payload)])

        async def brpop_side_effect(*args, **kwargs):
            try:
                return next(brpop_responses)
            except StopIteration:
                raise asyncio.CancelledError

        redis.brpop.side_effect = brpop_side_effect

        with (
            patch(
                "src.jobs.worker.run_analysis_job",
                side_effect=RuntimeError("transient error"),
            ),
            patch(
                "src.jobs.worker.requeue_raw_payload", new_callable=AsyncMock
            ) as mock_requeue,
        ):
            await run_worker(redis, settings)

        mock_requeue.assert_awaited_once_with(redis, raw_payload)

    @pytest.mark.asyncio
    async def test_unsupported_provider_is_dropped_not_requeued(self):
        """UnsupportedProviderError causes the job to be dropped, not requeued."""
        settings = _make_settings()
        redis = AsyncMock()
        job = _make_job()

        brpop_responses = iter([(QUEUE_KEY, job.model_dump_json())])

        async def brpop_side_effect(*args, **kwargs):
            try:
                return next(brpop_responses)
            except StopIteration:
                raise asyncio.CancelledError

        redis.brpop.side_effect = brpop_side_effect

        with (
            patch(
                "src.jobs.worker.run_analysis_job",
                side_effect=UnsupportedProviderError("unsupported"),
            ),
            patch(
                "src.jobs.worker.requeue_raw_payload", new_callable=AsyncMock
            ) as mock_requeue,
        ):
            await run_worker(redis, settings)

        mock_requeue.assert_not_called()

    @pytest.mark.asyncio
    async def test_malformed_payload_is_dropped_not_requeued(self):
        """A payload that fails schema validation is dropped, not requeued."""
        settings = _make_settings()
        redis = AsyncMock()
        bad_payload = b'{"not": "a valid job"}'

        brpop_responses = iter([(QUEUE_KEY, bad_payload)])

        async def brpop_side_effect(*args, **kwargs):
            try:
                return next(brpop_responses)
            except StopIteration:
                raise asyncio.CancelledError

        redis.brpop.side_effect = brpop_side_effect

        with patch(
            "src.jobs.worker.requeue_raw_payload", new_callable=AsyncMock
        ) as mock_requeue:
            await run_worker(redis, settings)

        mock_requeue.assert_not_called()

    @pytest.mark.asyncio
    async def test_requeue_failure_does_not_crash_worker_loop(self):
        """If requeue_raw_payload raises, the worker logs the error and keeps running."""
        settings = _make_settings()
        redis = AsyncMock()
        job = _make_job()

        brpop_responses = iter([(QUEUE_KEY, job.model_dump_json())])

        async def brpop_side_effect(*args, **kwargs):
            try:
                return next(brpop_responses)
            except StopIteration:
                raise asyncio.CancelledError

        redis.brpop.side_effect = brpop_side_effect

        async def failing_requeue(*args, **kwargs):
            raise OSError("Redis connection refused")

        with (
            patch(
                "src.jobs.worker.run_analysis_job",
                side_effect=RuntimeError("transient error"),
            ),
            patch(
                "src.jobs.worker.requeue_raw_payload",
                side_effect=failing_requeue,
            ),
        ):
            # Must not raise — worker should log and continue to the next iteration
            await run_worker(redis, settings)

        assert redis.brpop.await_count == 2

    @pytest.mark.asyncio
    async def test_http_400_send_failure_is_dropped_not_requeued(self):
        settings = _make_settings()
        redis = AsyncMock()
        job = _make_job()

        brpop_responses = iter([(QUEUE_KEY, job.model_dump_json())])

        async def brpop_side_effect(*args, **kwargs):
            try:
                return next(brpop_responses)
            except StopIteration:
                raise asyncio.CancelledError

        redis.brpop.side_effect = brpop_side_effect

        error = httpx.HTTPStatusError(
            "400 Bad Request",
            request=MagicMock(),
            response=MagicMock(status_code=400),
        )

        with (
            patch("src.jobs.worker.run_analysis_job", side_effect=error),
            patch("src.jobs.worker.requeue_raw_payload", new_callable=AsyncMock) as mock_requeue,
        ):
            await run_worker(redis, settings)

        mock_requeue.assert_not_called()

    @pytest.mark.asyncio
    async def test_apify_400_is_dropped_not_requeued(self):
        settings = _make_settings()
        redis = AsyncMock()
        job = _make_job()

        brpop_responses = iter([(QUEUE_KEY, job.model_dump_json())])

        async def brpop_side_effect(*args, **kwargs):
            try:
                return next(brpop_responses)
            except StopIteration:
                raise asyncio.CancelledError

        redis.brpop.side_effect = brpop_side_effect

        with (
            patch(
                "src.jobs.worker.run_analysis_job",
                side_effect=ApifyError("Apify actor run failed with status 400: invalid-input"),
            ),
            patch("src.jobs.worker.requeue_raw_payload", new_callable=AsyncMock) as mock_requeue,
        ):
            await run_worker(redis, settings)

        mock_requeue.assert_not_called()

    @pytest.mark.asyncio
    async def test_openrouter_500_is_requeued(self):
        settings = _make_settings()
        redis = AsyncMock()
        job = _make_job()

        brpop_responses = iter([(QUEUE_KEY, job.model_dump_json())])

        async def brpop_side_effect(*args, **kwargs):
            try:
                return next(brpop_responses)
            except StopIteration:
                raise asyncio.CancelledError

        redis.brpop.side_effect = brpop_side_effect

        with (
            patch(
                "src.jobs.worker.run_analysis_job",
                side_effect=OpenRouterError("OpenRouter request failed with status 500: upstream timeout"),
            ),
            patch("src.jobs.worker.requeue_raw_payload", new_callable=AsyncMock) as mock_requeue,
        ):
            await run_worker(redis, settings)

        mock_requeue.assert_awaited_once()


# ---------------------------------------------------------------------------
# process_job — framework integration (018)
# ---------------------------------------------------------------------------


class TestProcessJobFrameworkIntegration:
    """Prove that process_job routes analysis through the module framework."""

    @pytest.mark.asyncio
    async def test_module_runner_invoked_with_analysis_context(self):
        """process_job runs analysis via ModuleRunner, not a direct service call."""
        from src.analysis.context import AnalysisContext
        from src.analysis.runner import ModuleRunner

        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        captured_ctxs: list[AnalysisContext] = []
        original_run = ModuleRunner.run

        async def spy_run(self, ctx):  # type: ignore[override]
            captured_ctxs.append(ctx)
            return await original_run(self, ctx)

        with (
            patch.object(ModuleRunner, "run", spy_run),
            patch("src.telegram.presenter.send_message", new_callable=AsyncMock),
        ):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
            )

        assert len(captured_ctxs) == 1
        ctx = captured_ctxs[0]
        assert isinstance(ctx, AnalysisContext)
        assert ctx.listing is listing

    @pytest.mark.asyncio
    async def test_analysis_result_extracted_correctly_from_framework(self):
        """AnalysisResult coming through the framework matches the service output."""
        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        sent_texts: list[str] = []

        async def fake_send(token, chat_id, text, *, client=None):
            sent_texts.append(text)

        with patch("src.telegram.presenter.send_message", side_effect=fake_send):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
            )

        assert sent_texts
        assert result.summary in sent_texts[0]

    @pytest.mark.asyncio
    async def test_raw_payload_present_in_context_when_repo_provided(self):
        """AnalysisContext.raw_payload is set when raw_payload_repo is injected."""
        from src.analysis.context import AnalysisContext
        from src.analysis.runner import ModuleRunner
        from src.domain.raw_payload import RawPayload

        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        adapter_result = _make_adapter_result(listing)
        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=adapter_result)
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)
        mock_repo = AsyncMock()

        captured_ctxs: list[AnalysisContext] = []
        original_run = ModuleRunner.run

        async def spy_run(self, ctx):  # type: ignore[override]
            captured_ctxs.append(ctx)
            return await original_run(self, ctx)

        with (
            patch.object(ModuleRunner, "run", spy_run),
            patch("src.telegram.presenter.send_message", new_callable=AsyncMock),
        ):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
                raw_payload_repo=mock_repo,
            )

        assert len(captured_ctxs) == 1
        ctx = captured_ctxs[0]
        assert isinstance(ctx.raw_payload, RawPayload)
        assert ctx.raw_payload.provider == "airbnb"
        assert ctx.raw_payload.source_url == job.source_url

    @pytest.mark.asyncio
    async def test_raw_payload_present_in_context_even_without_repo(self):
        """AnalysisContext.raw_payload is populated from adapter_result.raw even when
        raw_payload_repo is None (no DB persistence requested)."""
        from src.analysis.context import AnalysisContext
        from src.analysis.runner import ModuleRunner
        from src.domain.raw_payload import RawPayload

        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        adapter_result = _make_adapter_result(listing)
        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=adapter_result)
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        captured_ctxs: list[AnalysisContext] = []
        original_run = ModuleRunner.run

        async def spy_run(self, ctx):  # type: ignore[override]
            captured_ctxs.append(ctx)
            return await original_run(self, ctx)

        with (
            patch.object(ModuleRunner, "run", spy_run),
            patch("src.telegram.presenter.send_message", new_callable=AsyncMock),
        ):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
                raw_payload_repo=None,
            )

        ctx = captured_ctxs[0]
        assert isinstance(ctx.raw_payload, RawPayload)
        assert ctx.raw_payload.payload == adapter_result.raw


# ---------------------------------------------------------------------------
# process_job — reviews module integration (019)
# ---------------------------------------------------------------------------


class TestProcessJobReviewsModuleIntegration:
    """Prove that process_job registers reviews modules and their results
    appear in module_results alongside AISummaryResult."""

    @pytest.mark.asyncio
    async def test_reviews_result_present_in_module_results(self):
        """process_job registers reviews modules; ReviewsResult appears in output."""
        from src.analysis.modules.reviews import ReviewsResult
        from src.analysis.modules.ai_summary import AISummaryResult
        from src.analysis.runner import ModuleRunner

        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        captured_results: list = []
        original_run = ModuleRunner.run

        async def spy_run(self, ctx):  # type: ignore[override]
            results = await original_run(self, ctx)
            captured_results.extend(results)
            return results

        with (
            patch.object(ModuleRunner, "run", spy_run),
            patch("src.telegram.presenter.send_message", new_callable=AsyncMock),
        ):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
            )

        result_types = {type(r) for r in captured_results}
        assert AISummaryResult in result_types
        assert ReviewsResult in result_types

    @pytest.mark.asyncio
    async def test_airbnb_reviews_module_registered_for_airbnb_listing(self):
        """AirbnbReviewsModule is resolved for Airbnb provider in process_job."""
        from src.analysis.modules.reviews import AirbnbReviewsModule, ReviewsResult
        from src.analysis.runner import ModuleRunner

        job = _make_job(provider=ListingProvider.AIRBNB)
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        captured_results: list = []
        original_run = ModuleRunner.run

        async def spy_run(self, ctx):  # type: ignore[override]
            results = await original_run(self, ctx)
            captured_results.extend(results)
            return results

        with (
            patch.object(ModuleRunner, "run", spy_run),
            patch("src.telegram.presenter.send_message", new_callable=AsyncMock),
        ):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
            )

        reviews_results = [r for r in captured_results if isinstance(r, ReviewsResult)]
        assert len(reviews_results) == 1
        # Module name must be "reviews"
        assert reviews_results[0].module_name == "reviews"

    @pytest.mark.asyncio
    async def test_airbnb_reviews_use_raw_payload_without_repo(self):
        """AirbnbReviewsModule can extract reviews from raw payload even when
        raw_payload_repo=None (no DB persistence).  ReviewsResult should reflect
        the review count from the adapter's raw payload."""
        from src.analysis.modules.reviews import ReviewsResult
        from src.analysis.runner import ModuleRunner

        job = _make_job(provider=ListingProvider.AIRBNB)
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        # Adapter returns a raw payload that contains Airbnb review data.
        raw_with_reviews = {
            "id": listing.source_id,
            "name": listing.title,
            "reviews": [{"comments": "Lovely place!"}],
            "reviewsCount": 7,
            "starRating": 4.8,
        }
        from src.adapters.base import AdapterResult
        adapter_result = AdapterResult(raw=raw_with_reviews, listing=listing)
        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=adapter_result)
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        captured_results: list = []
        original_run = ModuleRunner.run

        async def spy_run(self, ctx):  # type: ignore[override]
            results = await original_run(self, ctx)
            captured_results.extend(results)
            return results

        with (
            patch.object(ModuleRunner, "run", spy_run),
            patch("src.telegram.presenter.send_message", new_callable=AsyncMock),
        ):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
                raw_payload_repo=None,  # no DB — raw_payload must still be available
            )

        reviews_results = [r for r in captured_results if isinstance(r, ReviewsResult)]
        assert len(reviews_results) == 1
        # The module saw the raw payload and extracted the count from it.
        assert reviews_results[0].review_count == 7

    @pytest.mark.asyncio
    async def test_telegram_output_unchanged_with_reviews_module_registered(self):
        """Registering reviews modules does not change the Telegram message content."""
        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result(listing))
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        sent_texts: list[str] = []

        async def fake_send(token, chat_id, text, *, client=None):
            sent_texts.append(text)

        with patch("src.telegram.presenter.send_message", side_effect=fake_send):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
            )

        assert sent_texts
        assert "Cozy flat in Berlin" in sent_texts[0]
        assert "A pleasant flat in central Berlin." in sent_texts[0]

