"""Tests for analysis job creation, serialisation, and Redis enqueue."""

import json
import logging
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.listing import AnalysisJob, JobStatus, ListingProvider
from src.jobs.queue import (
    QUEUE_KEY,
    _IDEMPOTENCY_KEY_PREFIX,
    _IDEMPOTENCY_TTL_SECONDS,
    enqueue_analysis_job,
)


# ---------------------------------------------------------------------------
# AnalysisJob model
# ---------------------------------------------------------------------------


class TestAnalysisJobModel:
    def test_default_status_is_pending(self):
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/123",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1001,
            telegram_message_id=42,
        )
        assert job.status == JobStatus.PENDING

    def test_id_is_uuid(self):
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/123",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1001,
            telegram_message_id=42,
        )
        assert isinstance(job.id, uuid.UUID)

    def test_two_jobs_have_different_ids(self):
        make = lambda: AnalysisJob(
            source_url="https://www.airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1,
            telegram_message_id=1,
        )
        assert make().id != make().id

    def test_fields_are_stored_correctly(self):
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/999",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=5555,
            telegram_message_id=77,
        )
        assert job.source_url == "https://www.airbnb.com/rooms/999"
        assert job.provider == ListingProvider.AIRBNB
        assert job.telegram_chat_id == 5555
        assert job.telegram_message_id == 77

    def test_serialises_to_json_roundtrip(self):
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1,
            telegram_message_id=2,
        )
        json_str = job.model_dump_json()
        restored = AnalysisJob.model_validate_json(json_str)
        assert restored.id == job.id
        assert restored.source_url == job.source_url
        assert restored.provider == job.provider
        assert restored.status == job.status
        assert restored.telegram_chat_id == job.telegram_chat_id
        assert restored.telegram_message_id == job.telegram_message_id

    def test_serialised_provider_is_string_value(self):
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1,
            telegram_message_id=1,
        )
        data = json.loads(job.model_dump_json())
        assert data["provider"] == "airbnb"

    def test_serialised_status_is_string_value(self):
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1,
            telegram_message_id=1,
        )
        data = json.loads(job.model_dump_json())
        assert data["status"] == "pending"


# ---------------------------------------------------------------------------
# enqueue_analysis_job
# ---------------------------------------------------------------------------


class TestEnqueueAnalysisJob:
    @pytest.mark.asyncio
    async def test_eval_uses_queue_key_as_second_key(self):
        redis = AsyncMock()
        redis.eval.return_value = 1
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1,
            telegram_message_id=1,
        )
        await enqueue_analysis_job(redis, job)
        redis.eval.assert_awaited_once()
        # Positional args: script, numkeys, key1, key2, ttl, payload
        call_args = redis.eval.call_args[0]
        assert call_args[3] == QUEUE_KEY

    @pytest.mark.asyncio
    async def test_enqueued_payload_is_valid_json(self):
        redis = AsyncMock()
        redis.eval.return_value = 1
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/55",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=99,
            telegram_message_id=10,
        )
        await enqueue_analysis_job(redis, job)
        # ARGV[2] is the 6th positional arg (index 5)
        payload = redis.eval.call_args[0][5]
        data = json.loads(payload)
        assert data["source_url"] == "https://www.airbnb.com/rooms/55"
        assert data["telegram_chat_id"] == 99
        assert data["telegram_message_id"] == 10
        assert data["provider"] == "airbnb"

    @pytest.mark.asyncio
    async def test_enqueued_payload_roundtrips_to_analysis_job(self):
        redis = AsyncMock()
        redis.eval.return_value = 1
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/7",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=2,
            telegram_message_id=3,
        )
        await enqueue_analysis_job(redis, job)
        payload = redis.eval.call_args[0][5]
        restored = AnalysisJob.model_validate_json(payload)
        assert restored.id == job.id
        assert restored.provider == ListingProvider.AIRBNB
        assert restored.status == JobStatus.PENDING


# ---------------------------------------------------------------------------
# Idempotency guard: same chat/message pair must not enqueue twice
# ---------------------------------------------------------------------------


class TestEnqueueIdempotency:
    """enqueue_analysis_job is idempotent: the same (chat_id, message_id) pair
    must only reach LPUSH once even when the webhook is retried by Telegram."""

    def _make_job(self, chat_id: int = 1001, message_id: int = 5) -> AnalysisJob:
        return AnalysisJob(
            source_url="https://www.airbnb.com/rooms/123",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=chat_id,
            telegram_message_id=message_id,
        )

    @pytest.mark.asyncio
    async def test_idempotency_key_is_first_eval_key_with_ttl(self):
        """The Lua script receives the idempotency key as KEYS[1] and the TTL as ARGV[1]."""
        redis = AsyncMock()
        redis.eval.return_value = 1
        await enqueue_analysis_job(redis, self._make_job())
        redis.eval.assert_awaited_once()
        args = redis.eval.call_args[0]
        # args: script, numkeys=2, key1 (idempotency), key2 (queue), ttl, payload
        idempotency_key = args[2]
        ttl_arg = args[4]
        assert _IDEMPOTENCY_KEY_PREFIX in idempotency_key
        assert ttl_arg == str(_IDEMPOTENCY_TTL_SECONDS)

    @pytest.mark.asyncio
    async def test_idempotency_key_includes_chat_and_message_ids(self):
        redis = AsyncMock()
        redis.eval.return_value = 1
        await enqueue_analysis_job(redis, self._make_job(chat_id=42, message_id=99))
        key = redis.eval.call_args[0][2]
        assert _IDEMPOTENCY_KEY_PREFIX in key
        assert "42" in key
        assert "99" in key

    @pytest.mark.asyncio
    async def test_returns_true_when_newly_enqueued(self):
        """Lua script returns 1 when the key did not exist → function returns True."""
        redis = AsyncMock()
        redis.eval.return_value = 1
        result = await enqueue_analysis_job(redis, self._make_job())
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_already_enqueued(self):
        """Lua script returns 0 when the key already existed → function returns False."""
        redis = AsyncMock()
        redis.eval.return_value = 0
        result = await enqueue_analysis_job(redis, self._make_job())
        assert result is False

    @pytest.mark.asyncio
    async def test_single_atomic_eval_call_no_separate_set_or_lpush(self):
        """The idempotency check and queue push must be a single eval, not two calls.

        Two separate calls (SET NX then LPUSH) create a window where the key can
        be set but the push can fail, turning any transient Redis error into a
        permanently dropped job on retry.
        """
        redis = AsyncMock()
        redis.eval.return_value = 1
        await enqueue_analysis_job(redis, self._make_job())
        redis.eval.assert_awaited_once()
        redis.set.assert_not_awaited()
        redis.lpush.assert_not_awaited()


# ---------------------------------------------------------------------------
# App wiring: webhook enqueues job when Redis is available
# ---------------------------------------------------------------------------


def _test_settings(**overrides):
    from src.app.config import Settings

    defaults = {
        "app_env": "testing",
        "telegram_bot_token": "test-token",
        "openrouter_api_key": "test-key",
        "apify_api_token": "test-apify",
        "database_url": "postgresql://test:test@localhost:5432/test",
        "redis_url": "redis://localhost:6379/1",
    }
    defaults.update(overrides)
    return Settings(**defaults)


class TestWebhookEnqueueWiring:
    """Verify the webhook calls enqueue_analysis_job when Redis is available."""

    def _airbnb_payload(self, chat_id: int = 1001, message_id: int = 5) -> dict:
        return {
            "update_id": 1,
            "message": {
                "message_id": message_id,
                "from": {"id": 42, "first_name": "Alice"},
                "chat": {"id": chat_id, "type": "private"},
                "text": "https://www.airbnb.com/rooms/123",
            },
        }

    @patch("src.telegram.router.get_chat_language", new_callable=AsyncMock)
    @patch("src.telegram.router.enqueue_analysis_job", new_callable=AsyncMock)
    @patch("src.telegram.router.send_message_return_id", new_callable=AsyncMock)
    def test_enqueue_called_when_redis_available(self, mock_send_id, mock_enqueue, mock_get_lang):
        from fastapi.testclient import TestClient

        from src.app.main import create_app
        from src.i18n.types import Language

        mock_get_lang.return_value = Language.RU
        mock_send_id.return_value = 999

        app = create_app(settings=_test_settings())
        mock_redis = MagicMock()
        app.state.redis = mock_redis

        # TestClient without context manager: lifespan does not run, so
        # app.state.redis stays as the mock we injected above.
        client = TestClient(app, raise_server_exceptions=True)
        response = client.post("/telegram/webhook", json=self._airbnb_payload())

        assert response.status_code == 200
        mock_enqueue.assert_awaited_once()
        enqueue_args = mock_enqueue.call_args[0]
        assert enqueue_args[0] is mock_redis
        job: AnalysisJob = enqueue_args[1]
        assert isinstance(job, AnalysisJob)
        assert job.source_url == "https://www.airbnb.com/rooms/123"
        assert job.provider == ListingProvider.AIRBNB
        assert job.telegram_chat_id == 1001
        assert job.telegram_message_id == 5

    @patch("src.telegram.router.enqueue_analysis_job", new_callable=AsyncMock)
    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_enqueue_skipped_when_redis_is_none(self, mock_send, mock_enqueue):
        """Without a Redis connection, enqueue is skipped and a 502 is returned so Telegram retries."""
        from fastapi.testclient import TestClient

        from src.app.main import create_app

        app = create_app(settings=_test_settings())
        # app.state.redis is None by default (no lifespan run in TestClient without context)

        client = TestClient(app)
        response = client.post("/telegram/webhook", json=self._airbnb_payload())
        assert response.status_code == 502
        mock_enqueue.assert_not_awaited()
        mock_send.assert_not_awaited()

    @patch("src.telegram.router.enqueue_analysis_job", new_callable=AsyncMock)
    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_warning_logged_when_redis_is_none(self, mock_send, mock_enqueue, caplog):
        """A WARNING must be emitted when Redis is unavailable and the request gets a 502."""
        from fastapi.testclient import TestClient

        from src.app.main import create_app

        app = create_app(settings=_test_settings())
        # app.state.redis is None by default

        client = TestClient(app)
        with caplog.at_level(logging.WARNING, logger="src.telegram.router"):
            response = client.post("/telegram/webhook", json=self._airbnb_payload())

        assert response.status_code == 502
        assert any("Redis" in r.message or "redis" in r.message.lower() for r in caplog.records)
        mock_enqueue.assert_not_awaited()
        mock_send.assert_not_awaited()

    @patch("src.telegram.router.get_chat_language", new_callable=AsyncMock)
    @patch("src.telegram.router.enqueue_analysis_job", new_callable=AsyncMock)
    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_enqueue_not_called_for_unsupported_url(self, mock_send, mock_enqueue, mock_get_lang):
        from fastapi.testclient import TestClient

        from src.app.main import create_app
        from src.i18n.types import Language

        mock_get_lang.return_value = Language.RU

        app = create_app(settings=_test_settings())
        app.state.redis = MagicMock()

        client = TestClient(app)
        payload = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "from": {"id": 42, "first_name": "Alice"},
                "chat": {"id": 1001, "type": "private"},
                "text": "https://www.booking.com/hotel/xyz",
            },
        }
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 200
        mock_enqueue.assert_not_awaited()
