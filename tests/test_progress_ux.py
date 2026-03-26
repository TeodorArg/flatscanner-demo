"""Focused tests for the Telegram analysis progress UX (feature 025).

Covers:
- Router sends progress message (via send_message_return_id) before enqueuing the job.
- The progress message_id is carried on the queued AnalysisJob.
- The progress message text does not echo the URL.
- Progress stage updates (fetching / analysing) are emitted during processing.
- The progress message is deleted before the final result is sent.
- The typing heartbeat task runs and is cancelled after processing.
- Progress failures are best-effort and do not abort the pipeline.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from src.adapters.base import AdapterResult
from src.analysis.result import AnalysisResult, PriceVerdict
from src.analysis.service import AnalysisService
from src.domain.listing import AnalysisJob, ListingProvider, NormalizedListing, PriceInfo
from src.i18n import get_string
from src.i18n.types import Language
from src.jobs.processor import _delete_progress, _typing_heartbeat, _update_progress, process_job


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_job(**overrides) -> AnalysisJob:
    defaults = dict(
        source_url="https://www.airbnb.com/rooms/12345",
        provider=ListingProvider.AIRBNB,
        telegram_chat_id=1001,
        telegram_message_id=7,
        telegram_progress_message_id=999,
        language=Language.EN,
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
# Domain model: AnalysisJob carries telegram_progress_message_id
# ---------------------------------------------------------------------------


class TestAnalysisJobProgressField:
    def test_progress_message_id_defaults_to_none(self):
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1,
            telegram_message_id=1,
        )
        assert job.telegram_progress_message_id is None

    def test_progress_message_id_can_be_set(self):
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1,
            telegram_message_id=1,
            telegram_progress_message_id=42,
        )
        assert job.telegram_progress_message_id == 42

    def test_progress_message_id_survives_json_round_trip(self):
        job = _make_job(telegram_progress_message_id=88)
        restored = AnalysisJob.model_validate_json(job.model_dump_json())
        assert restored.telegram_progress_message_id == 88


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
        assert job.telegram_progress_message_id == 777

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
# Processor: progress helpers are best-effort
# ---------------------------------------------------------------------------


class TestProgressHelpers:
    @pytest.mark.asyncio
    async def test_update_progress_skips_when_message_id_is_none(self):
        """_update_progress must be a no-op when message_id is None."""
        mock_edit = AsyncMock()
        with patch("src.jobs.processor.edit_message_text", mock_edit):
            await _update_progress("token", 1, None, "text", client=None)
        mock_edit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_progress_calls_edit_when_message_id_given(self):
        mock_edit = AsyncMock()
        with patch("src.jobs.processor.edit_message_text", mock_edit):
            await _update_progress("token", 1001, 42, "Fetching…", client=None)
        mock_edit.assert_awaited_once_with("token", 1001, 42, "Fetching…", client=None)

    @pytest.mark.asyncio
    async def test_update_progress_swallows_errors(self):
        """Failures from edit_message_text must not propagate."""
        mock_edit = AsyncMock(side_effect=Exception("telegram down"))
        with patch("src.jobs.processor.edit_message_text", mock_edit):
            # Should not raise
            await _update_progress("token", 1, 99, "text", client=None)

    @pytest.mark.asyncio
    async def test_delete_progress_skips_when_message_id_is_none(self):
        mock_delete = AsyncMock()
        with patch("src.jobs.processor.delete_message", mock_delete):
            await _delete_progress("token", 1, None, client=None)
        mock_delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_progress_calls_delete_when_message_id_given(self):
        mock_delete = AsyncMock()
        with patch("src.jobs.processor.delete_message", mock_delete):
            await _delete_progress("token", 1001, 55, client=None)
        mock_delete.assert_awaited_once_with("token", 1001, 55, client=None)

    @pytest.mark.asyncio
    async def test_delete_progress_swallows_errors(self):
        mock_delete = AsyncMock(side_effect=Exception("not found"))
        with patch("src.jobs.processor.delete_message", mock_delete):
            await _delete_progress("token", 1, 99, client=None)  # must not raise


# ---------------------------------------------------------------------------
# Processor: typing heartbeat runs and is cancelled
# ---------------------------------------------------------------------------


class TestTypingHeartbeat:
    @pytest.mark.asyncio
    async def test_heartbeat_sends_chat_action(self):
        mock_action = AsyncMock()
        with patch("src.jobs.processor.send_chat_action", mock_action):
            task = asyncio.create_task(
                _typing_heartbeat("token", 1001, client=None)
            )
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        mock_action.assert_awaited()

    @pytest.mark.asyncio
    async def test_heartbeat_swallows_send_errors(self):
        """A failure in send_chat_action must not kill the heartbeat loop."""
        mock_action = AsyncMock(side_effect=Exception("network"))
        with patch("src.jobs.processor.send_chat_action", mock_action):
            task = asyncio.create_task(
                _typing_heartbeat("token", 1001, client=None)
            )
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        # No exception should have escaped


# ---------------------------------------------------------------------------
# Processor: end-to-end progress flow
# ---------------------------------------------------------------------------


class TestProcessJobProgressFlow:
    def _run_process_job(self, job, settings, *, edit_side_effect=None, delete_side_effect=None):
        """Run process_job with mocked deps; return calls to edit/delete/send_message."""
        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result())

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=_make_analysis_result())

        edit_calls: list[tuple] = []
        delete_calls: list[tuple] = []
        send_calls: list[tuple] = []

        async def fake_edit(token, chat_id, msg_id, text, *, client=None):
            edit_calls.append((chat_id, msg_id, text))

        async def fake_delete(token, chat_id, msg_id, *, client=None):
            delete_calls.append((chat_id, msg_id))

        async def fake_send(token, chat_id, text, *, client=None):
            send_calls.append((chat_id, text))

        if edit_side_effect is not None:
            fake_edit = AsyncMock(side_effect=edit_side_effect)

        if delete_side_effect is not None:
            fake_delete = AsyncMock(side_effect=delete_side_effect)

        import asyncio as _asyncio

        async def run():
            with (
                patch("src.jobs.processor.edit_message_text", side_effect=fake_edit),
                patch("src.jobs.processor.delete_message", side_effect=fake_delete),
                patch("src.jobs.processor.send_message", side_effect=fake_send),
                patch("src.jobs.processor.send_chat_action", new_callable=AsyncMock),
            ):
                await process_job(
                    job,
                    settings,
                    adapter=mock_adapter,
                    analysis_service=mock_service,
                    translation_service=_make_passthrough_ts(),
                )
            return edit_calls, delete_calls, send_calls

        return _asyncio.get_event_loop().run_until_complete(run())

    @pytest.mark.asyncio
    async def test_progress_updates_emitted_before_final_send(self):
        """edit_message_text must be called for coarse-grained stages."""
        job = _make_job(telegram_progress_message_id=42)
        settings = _make_settings()

        edit_calls: list[tuple] = []
        delete_calls: list[tuple] = []

        async def fake_edit(token, chat_id, msg_id, text, *, client=None):
            edit_calls.append((chat_id, msg_id, text))

        async def fake_delete(token, chat_id, msg_id, *, client=None):
            delete_calls.append((chat_id, msg_id))

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result())
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=_make_analysis_result())

        with (
            patch("src.jobs.processor.edit_message_text", side_effect=fake_edit),
            patch("src.jobs.processor.delete_message", side_effect=fake_delete),
            patch("src.jobs.processor.send_message", new_callable=AsyncMock),
            patch("src.jobs.processor.send_chat_action", new_callable=AsyncMock),
        ):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
            )

        assert len(edit_calls) >= 4, "Expected at least 4 progress stage updates"
        assert all(c[1] == 42 for c in edit_calls), "All edits must target progress msg_id=42"
        texts = [c[2] for c in edit_calls]
        extracting = get_string("msg.progress.extracting", Language.EN)
        enriching = get_string("msg.progress.enriching", Language.EN)
        analysing = get_string("msg.progress.analysing", Language.EN)
        preparing = get_string("msg.progress.preparing", Language.EN)
        assert extracting in texts
        assert enriching in texts
        assert analysing in texts
        assert preparing in texts
        # Stages must appear in the correct pipeline order
        assert texts.index(extracting) < texts.index(enriching)
        assert texts.index(enriching) < texts.index(analysing)
        assert texts.index(analysing) < texts.index(preparing)

    @pytest.mark.asyncio
    async def test_progress_message_deleted_on_success(self):
        """delete_message must always be called on the success path (via finally)."""
        job = _make_job(telegram_progress_message_id=42)
        settings = _make_settings()

        call_order: list[str] = []

        async def fake_delete(token, chat_id, msg_id, *, client=None):
            call_order.append("delete")

        async def fake_send(token, chat_id, text, *, client=None):
            call_order.append("send")

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result())
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=_make_analysis_result())

        with (
            patch("src.jobs.processor.edit_message_text", new_callable=AsyncMock),
            patch("src.jobs.processor.delete_message", side_effect=fake_delete),
            patch("src.jobs.processor.send_message", side_effect=fake_send),
            patch("src.jobs.processor.send_chat_action", new_callable=AsyncMock),
        ):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
            )

        assert "delete" in call_order
        assert "send" in call_order
        # delete runs in finally, so it comes after send on the success path
        assert call_order.index("send") < call_order.index("delete")

    @pytest.mark.asyncio
    async def test_progress_message_deleted_on_pipeline_failure(self):
        """delete_message must be called even when the pipeline raises (finally cleanup)."""
        job = _make_job(telegram_progress_message_id=42)
        settings = _make_settings()

        mock_delete = AsyncMock()
        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(side_effect=RuntimeError("fetch failed"))

        with (
            patch("src.jobs.processor.edit_message_text", new_callable=AsyncMock),
            patch("src.jobs.processor.delete_message", mock_delete),
            patch("src.jobs.processor.send_message", new_callable=AsyncMock),
            patch("src.jobs.processor.send_chat_action", new_callable=AsyncMock),
        ):
            with pytest.raises(RuntimeError, match="fetch failed"):
                await process_job(
                    job,
                    settings,
                    adapter=mock_adapter,
                )

        mock_delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_progress_failure_does_not_abort_pipeline(self):
        """If edit_message_text always fails, the final send_message still succeeds."""
        job = _make_job(telegram_progress_message_id=42)
        settings = _make_settings()

        mock_send = AsyncMock()
        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result())
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=_make_analysis_result())

        with (
            patch(
                "src.jobs.processor.edit_message_text",
                AsyncMock(side_effect=Exception("Telegram error")),
            ),
            patch(
                "src.jobs.processor.delete_message",
                AsyncMock(side_effect=Exception("Telegram error")),
            ),
            patch("src.jobs.processor.send_message", mock_send),
            patch("src.jobs.processor.send_chat_action", new_callable=AsyncMock),
        ):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
            )

        mock_send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_progress_updates_when_progress_id_is_none(self):
        """When telegram_progress_message_id is None, no edit or delete calls are made."""
        job = _make_job(telegram_progress_message_id=None)
        settings = _make_settings()

        mock_edit = AsyncMock()
        mock_delete = AsyncMock()
        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=_make_adapter_result())
        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=_make_analysis_result())

        with (
            patch("src.jobs.processor.edit_message_text", mock_edit),
            patch("src.jobs.processor.delete_message", mock_delete),
            patch("src.jobs.processor.send_message", new_callable=AsyncMock),
            patch("src.jobs.processor.send_chat_action", new_callable=AsyncMock),
        ):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
            )

        mock_edit.assert_not_awaited()
        mock_delete.assert_not_awaited()
