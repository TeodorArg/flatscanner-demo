"""Focused tests for the Telegram analysis progress UX (features 025/026).

Covers:
- Router sends progress message (via send_message_return_id) before enqueuing the job.
- The progress message_id is carried on the queued AnalysisJob.
- The progress message text does not echo the URL.
- TelegramProgressSink emits stage updates and cleans up correctly.
- The typing heartbeat task runs and is cancelled after processing.
- Progress failures are best-effort and do not abort the pipeline.
- process_job delegates progress reporting to the injected ProgressSink.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.adapters.base import AdapterResult
from src.analysis.result import AnalysisResult, PriceVerdict
from src.analysis.service import AnalysisService
from src.domain.delivery import DeliveryChannel, ProgressSink, TelegramDeliveryContext
from src.domain.listing import AnalysisJob, ListingProvider, NormalizedListing, PriceInfo
from src.i18n import get_string
from src.i18n.types import Language
from src.jobs.processor import process_job
from src.telegram.progress import TelegramProgressSink


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_job(
    *,
    progress_message_id: int | None = 999,
    chat_id: int = 1001,
    message_id: int = 7,
    language: Language = Language.EN,
    **overrides,
) -> AnalysisJob:
    return AnalysisJob(
        source_url="https://www.airbnb.com/rooms/12345",
        provider=ListingProvider.AIRBNB,
        delivery_channel=DeliveryChannel.TELEGRAM,
        telegram_context=TelegramDeliveryContext(
            chat_id=chat_id,
            message_id=message_id,
            progress_message_id=progress_message_id,
        ),
        language=language,
        **overrides,
    )


def _make_listing() -> NormalizedListing:
    return NormalizedListing(
        provider=ListingProvider.AIRBNB,
        source_url="https://www.airbnb.com/rooms/12345",
        source_id="12345",
        title="Cozy flat in Berlin",
        price=PriceInfo(amount=Decimal("80"), currency="EUR"),
    )


def _make_adapter_result(listing: NormalizedListing | None = None) -> AdapterResult:
    if listing is None:
        listing = _make_listing()
    return AdapterResult(raw={"id": listing.source_id, "name": listing.title}, listing=listing)


def _make_analysis_result() -> AnalysisResult:
    return AnalysisResult(
        display_title="Cozy flat in Berlin",
        summary="A pleasant flat.",
        strengths=["Central location"],
        risks=[],
        price_verdict=PriceVerdict.FAIR,
        price_explanation="Fair price.",
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
    from src.translation.service import TranslationService

    mock_ts = MagicMock(spec=TranslationService)
    mock_ts.translate = AsyncMock(side_effect=lambda result, lang: result)
    return mock_ts


# ---------------------------------------------------------------------------
# i18n catalog: msg.analysing must not contain a URL placeholder
# ---------------------------------------------------------------------------


class TestAnalysingString:
    def test_analysing_string_has_no_url_placeholder_en(self):
        text = get_string("msg.analysing", Language.EN)
        assert "{url}" not in text
        assert "http" not in text

    def test_analysing_string_has_no_url_placeholder_ru(self):
        text = get_string("msg.analysing", Language.RU)
        assert "{url}" not in text
        assert "http" not in text

    def test_analysing_string_mentions_two_minutes_en(self):
        text = get_string("msg.analysing", Language.EN)
        assert "2 minute" in text or "2-minute" in text or "two minute" in text.lower() or "2 min" in text

    def test_analysing_string_mentions_two_minutes_ru(self):
        text = get_string("msg.analysing", Language.RU)
        assert "2 " in text or "минут" in text

    def test_progress_extracting_key_exists_for_all_languages(self):
        for lang in Language:
            text = get_string("msg.progress.extracting", lang)
            assert text

    def test_progress_analysing_key_exists_for_all_languages(self):
        for lang in Language:
            text = get_string("msg.progress.analysing", lang)
            assert text

    def test_progress_enriching_key_exists_for_all_languages(self):
        for lang in Language:
            text = get_string("msg.progress.enriching", lang)
            assert text

    def test_progress_preparing_key_exists_for_all_languages(self):
        for lang in Language:
            text = get_string("msg.progress.preparing", lang)
            assert text


# ---------------------------------------------------------------------------
# Domain model: TelegramDeliveryContext carries progress_message_id
# ---------------------------------------------------------------------------


class TestAnalysisJobProgressField:
    def test_progress_message_id_defaults_to_none(self):
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            delivery_channel=DeliveryChannel.TELEGRAM,
            telegram_context=TelegramDeliveryContext(chat_id=1, message_id=1),
        )
        assert job.telegram_context.progress_message_id is None

    def test_progress_message_id_can_be_set(self):
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            delivery_channel=DeliveryChannel.TELEGRAM,
            telegram_context=TelegramDeliveryContext(chat_id=1, message_id=1, progress_message_id=42),
        )
        assert job.telegram_context.progress_message_id == 42

    def test_progress_message_id_survives_json_round_trip(self):
        job = _make_job(progress_message_id=88)
        restored = AnalysisJob.model_validate_json(job.model_dump_json())
        assert restored.telegram_context.progress_message_id == 88


# ---------------------------------------------------------------------------
# Router: progress message sent before enqueue, id carried on job
# ---------------------------------------------------------------------------


class TestRouterProgressMessage:
    """Integration-level tests via the FastAPI test client."""

    def _make_app_client(self, **settings_overrides):
        from fastapi.testclient import TestClient

        from src.app.main import create_app
        from src.app.config import Settings

        defaults = {
            "app_env": "testing",
            "telegram_bot_token": "test-token",
            "openrouter_api_key": "test-key",
            "apify_api_token": "test-apify",
            "database_url": "postgresql://test:test@localhost:5432/test",
            "redis_url": "redis://localhost:6379/1",
        }
        defaults.update(settings_overrides)
        app = create_app(settings=Settings(**defaults))
        mock_redis = AsyncMock()
        mock_redis.eval.return_value = 1
        app.state.redis = mock_redis
        client = TestClient(app)
        return client, mock_redis

    def _analyse_payload(self, chat_id: int = 1001) -> dict:
        return {
            "update_id": 1,
            "message": {
                "message_id": 7,
                "from": {"id": 42, "first_name": "Alice"},
                "chat": {"id": chat_id, "type": "private"},
                "text": "https://www.airbnb.com/rooms/12345",
            },
        }

    @patch("src.telegram.router.send_message_return_id", new_callable=AsyncMock)
    def test_progress_message_sent_before_enqueue(self, mock_send_id):
        """send_message_return_id must be called; the returned id lands on the enqueued job."""
        mock_send_id.return_value = 999
        client, mock_redis = self._make_app_client()

        call_order: list[str] = []

        async def track_send(*args, **kwargs):
            call_order.append("send")
            return 999

        async def track_eval(*args, **kwargs):
            call_order.append("eval")
            return 1

        mock_send_id.side_effect = track_send
        mock_redis.eval.side_effect = track_eval

        response = client.post("/telegram/webhook", json=self._analyse_payload())
        assert response.status_code == 200
        assert call_order == ["send", "eval"], "Progress message must be sent before enqueue"

    @patch("src.telegram.router.send_message_return_id", new_callable=AsyncMock)
    def test_progress_message_id_carried_on_job(self, mock_send_id):
        """The message_id from send_message_return_id must appear on the queued job."""
        mock_send_id.return_value = 777
        client, mock_redis = self._make_app_client()
        client.post("/telegram/webhook", json=self._analyse_payload())

        # The job JSON is the last positional arg passed to redis.eval
        eval_call = mock_redis.eval.call_args
        job_json = eval_call[0][-1]  # last positional arg is the serialised job
        job = AnalysisJob.model_validate_json(job_json)
        assert job.telegram_context.progress_message_id == 777

    @patch("src.telegram.router.send_message_return_id", new_callable=AsyncMock)
    def test_progress_message_text_has_no_url(self, mock_send_id):
        """The progress message must not echo the submitted URL."""
        mock_send_id.return_value = 999
        client, _ = self._make_app_client()
        client.post("/telegram/webhook", json=self._analyse_payload())
        call_args = mock_send_id.call_args[0]
        assert "airbnb.com/rooms/12345" not in call_args[2]

    @patch("src.telegram.router.delete_message", new_callable=AsyncMock)
    @patch("src.telegram.router.send_message_return_id", new_callable=AsyncMock)
    def test_progress_message_deleted_on_enqueue_failure(self, mock_send_id, mock_delete):
        """If enqueue (redis.eval) fails, the progress message must be best-effort deleted."""
        import redis.asyncio as aioredis

        mock_send_id.return_value = 555
        client, mock_redis = self._make_app_client()
        mock_redis.eval.side_effect = aioredis.RedisError("connection refused")

        response = client.post("/telegram/webhook", json=self._analyse_payload())

        assert response.status_code == 502
        mock_delete.assert_awaited_once()
        # delete_message must be called with the id returned by send_message_return_id
        args = mock_delete.call_args[0]
        assert args[2] == 555  # chat_id is args[1], message_id is args[2]


# ---------------------------------------------------------------------------
# TelegramProgressSink: progress helpers are best-effort
# ---------------------------------------------------------------------------


class TestTelegramProgressSink:
    @pytest.mark.asyncio
    async def test_update_skips_when_message_id_is_none(self):
        """update() must be a no-op when progress_message_id is None."""
        mock_edit = AsyncMock()
        with patch("src.telegram.progress.edit_message_text", mock_edit):
            sink = TelegramProgressSink("token", 1, None)
            await sink.update("text")
        mock_edit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_calls_edit_when_message_id_given(self):
        mock_edit = AsyncMock()
        with patch("src.telegram.progress.edit_message_text", mock_edit):
            sink = TelegramProgressSink("token", 1001, 42)
            await sink.update("Fetching…")
        mock_edit.assert_awaited_once_with("token", 1001, 42, "Fetching…", client=None)

    @pytest.mark.asyncio
    async def test_update_swallows_errors(self):
        """Failures from edit_message_text must not propagate."""
        mock_edit = AsyncMock(side_effect=Exception("telegram down"))
        with patch("src.telegram.progress.edit_message_text", mock_edit):
            sink = TelegramProgressSink("token", 1, 99)
            await sink.update("text")  # must not raise

    @pytest.mark.asyncio
    async def test_complete_skips_delete_when_message_id_is_none(self):
        mock_delete = AsyncMock()
        with patch("src.telegram.progress.delete_message", mock_delete):
            sink = TelegramProgressSink("token", 1, None)
            await sink.complete()
        mock_delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_complete_calls_delete_when_message_id_given(self):
        mock_delete = AsyncMock()
        with patch("src.telegram.progress.delete_message", mock_delete):
            sink = TelegramProgressSink("token", 1001, 55)
            await sink.complete()
        mock_delete.assert_awaited_once_with("token", 1001, 55, client=None)

    @pytest.mark.asyncio
    async def test_complete_swallows_delete_errors(self):
        mock_delete = AsyncMock(side_effect=Exception("not found"))
        with patch("src.telegram.progress.delete_message", mock_delete):
            sink = TelegramProgressSink("token", 1, 99)
            await sink.complete()  # must not raise

    @pytest.mark.asyncio
    async def test_fail_skips_delete_when_message_id_is_none(self):
        mock_delete = AsyncMock()
        with patch("src.telegram.progress.delete_message", mock_delete):
            sink = TelegramProgressSink("token", 1, None)
            await sink.fail()
        mock_delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_fail_calls_delete_when_message_id_given(self):
        mock_delete = AsyncMock()
        with patch("src.telegram.progress.delete_message", mock_delete):
            sink = TelegramProgressSink("token", 1001, 55)
            await sink.fail()
        mock_delete.assert_awaited_once_with("token", 1001, 55, client=None)

    @pytest.mark.asyncio
    async def test_fail_swallows_delete_errors(self):
        mock_delete = AsyncMock(side_effect=Exception("not found"))
        with patch("src.telegram.progress.delete_message", mock_delete):
            sink = TelegramProgressSink("token", 1, 99)
            await sink.fail()  # must not raise

    @pytest.mark.asyncio
    async def test_start_creates_heartbeat(self):
        """start() must launch a background heartbeat task."""
        mock_action = AsyncMock()
        with patch("src.telegram.progress.send_chat_action", mock_action):
            sink = TelegramProgressSink("token", 1001, None)
            await sink.start()
            await asyncio.sleep(0.05)
            assert sink._heartbeat is not None
            sink._heartbeat.cancel()
            try:
                await sink._heartbeat
            except asyncio.CancelledError:
                pass
        mock_action.assert_awaited()

    @pytest.mark.asyncio
    async def test_complete_cancels_heartbeat(self):
        """complete() must cancel the heartbeat started by start()."""
        mock_action = AsyncMock()
        mock_delete = AsyncMock()
        with (
            patch("src.telegram.progress.send_chat_action", mock_action),
            patch("src.telegram.progress.delete_message", mock_delete),
        ):
            sink = TelegramProgressSink("token", 1001, 42)
            await sink.start()
            assert sink._heartbeat is not None
            await sink.complete()
        assert sink._heartbeat.cancelled() or sink._heartbeat.done()

    @pytest.mark.asyncio
    async def test_fail_cancels_heartbeat(self):
        """fail() must cancel the heartbeat started by start()."""
        mock_action = AsyncMock()
        mock_delete = AsyncMock()
        with (
            patch("src.telegram.progress.send_chat_action", mock_action),
            patch("src.telegram.progress.delete_message", mock_delete),
        ):
            sink = TelegramProgressSink("token", 1001, 42)
            await sink.start()
            assert sink._heartbeat is not None
            await sink.fail()
        assert sink._heartbeat.cancelled() or sink._heartbeat.done()

    @pytest.mark.asyncio
    async def test_heartbeat_swallows_send_errors(self):
        """A failure in send_chat_action must not kill the heartbeat loop."""
        mock_action = AsyncMock(side_effect=Exception("network"))
        with patch("src.telegram.progress.send_chat_action", mock_action):
            sink = TelegramProgressSink("token", 1001, None)
            task = asyncio.create_task(sink._run_heartbeat())
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        # No exception should have escaped


# ---------------------------------------------------------------------------
# Processor: progress flow delegated to ProgressSink
# ---------------------------------------------------------------------------


class SpyProgressSink:
    """Test double that records calls to the ProgressSink interface."""

    def __init__(self):
        self.started = False
        self.updates: list[str] = []
        self.completed = False
        self.failed = False

    async def start(self) -> None:
        self.started = True

    async def update(self, text: str) -> None:
        self.updates.append(text)

    async def complete(self) -> None:
        self.completed = True

    async def fail(self) -> None:
        self.failed = True


class TestProcessJobProgressFlow:
    def _make_mock_adapter(self):
        mock = MagicMock()
        mock.fetch = AsyncMock(return_value=_make_adapter_result())
        return mock

    def _make_mock_service(self):
        mock = MagicMock(spec=AnalysisService)
        mock.analyse = AsyncMock(return_value=_make_analysis_result())
        return mock

    @pytest.mark.asyncio
    async def test_progress_sink_receives_all_stages(self):
        """The injected ProgressSink must receive update() for each pipeline stage."""
        job = _make_job(progress_message_id=42)
        settings = _make_settings()
        spy = SpyProgressSink()

        with patch("src.telegram.presenter.send_message", new_callable=AsyncMock):
            await process_job(
                job,
                settings,
                adapter=self._make_mock_adapter(),
                analysis_service=self._make_mock_service(),
                translation_service=_make_passthrough_ts(),
                progress_sink=spy,
            )

        assert spy.started
        assert len(spy.updates) >= 4, "Expected at least 4 stage updates"
        extracting = get_string("msg.progress.extracting", Language.EN)
        enriching = get_string("msg.progress.enriching", Language.EN)
        analysing = get_string("msg.progress.analysing", Language.EN)
        preparing = get_string("msg.progress.preparing", Language.EN)
        assert extracting in spy.updates
        assert enriching in spy.updates
        assert analysing in spy.updates
        assert preparing in spy.updates
        # Order must match pipeline flow
        assert spy.updates.index(extracting) < spy.updates.index(enriching)
        assert spy.updates.index(enriching) < spy.updates.index(analysing)
        assert spy.updates.index(analysing) < spy.updates.index(preparing)

    @pytest.mark.asyncio
    async def test_sink_complete_called_on_success(self):
        """complete() must be called when the pipeline succeeds."""
        job = _make_job(progress_message_id=42)
        settings = _make_settings()
        spy = SpyProgressSink()

        with patch("src.telegram.presenter.send_message", new_callable=AsyncMock):
            await process_job(
                job,
                settings,
                adapter=self._make_mock_adapter(),
                analysis_service=self._make_mock_service(),
                translation_service=_make_passthrough_ts(),
                progress_sink=spy,
            )

        assert spy.completed
        assert not spy.failed

    @pytest.mark.asyncio
    async def test_sink_fail_called_on_pipeline_failure(self):
        """fail() must be called when the pipeline raises."""
        job = _make_job(progress_message_id=42)
        settings = _make_settings()
        spy = SpyProgressSink()

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(side_effect=RuntimeError("fetch failed"))

        with pytest.raises(RuntimeError, match="fetch failed"):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                progress_sink=spy,
            )

        assert spy.failed
        assert not spy.completed

    @pytest.mark.asyncio
    async def test_default_sink_is_telegram_when_none_injected(self):
        """When progress_sink=None, processor builds a TelegramProgressSink by default."""
        job = _make_job(progress_message_id=42)
        settings = _make_settings()

        edit_calls: list = []
        delete_calls: list = []

        async def fake_edit(token, chat_id, msg_id, text, *, client=None):
            edit_calls.append((chat_id, msg_id, text))

        async def fake_delete(token, chat_id, msg_id, *, client=None):
            delete_calls.append((chat_id, msg_id))

        with (
            patch("src.telegram.progress.edit_message_text", side_effect=fake_edit),
            patch("src.telegram.progress.delete_message", side_effect=fake_delete),
            patch("src.telegram.progress.send_chat_action", new_callable=AsyncMock),
            patch("src.telegram.presenter.send_message", new_callable=AsyncMock),
        ):
            await process_job(
                job,
                settings,
                adapter=self._make_mock_adapter(),
                analysis_service=self._make_mock_service(),
                translation_service=_make_passthrough_ts(),
            )

        assert len(edit_calls) >= 4
        assert len(delete_calls) == 1

    @pytest.mark.asyncio
    async def test_default_sink_swallows_telegram_api_failures(self):
        """TelegramProgressSink must not abort the pipeline when Telegram API calls fail."""
        job = _make_job(progress_message_id=42)
        settings = _make_settings()
        mock_send = AsyncMock()

        with (
            patch(
                "src.telegram.progress.edit_message_text",
                AsyncMock(side_effect=Exception("Telegram error")),
            ),
            patch(
                "src.telegram.progress.delete_message",
                AsyncMock(side_effect=Exception("Telegram error")),
            ),
            patch("src.telegram.progress.send_chat_action", new_callable=AsyncMock),
            patch("src.telegram.presenter.send_message", mock_send),
        ):
            await process_job(
                job,
                settings,
                adapter=self._make_mock_adapter(),
                analysis_service=self._make_mock_service(),
                translation_service=_make_passthrough_ts(),
            )

        mock_send.assert_awaited_once()

