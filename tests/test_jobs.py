"""Tests for analysis job creation, serialisation, and Redis enqueue."""

import json
import logging
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.listing import AnalysisJob, JobStatus, ListingProvider
from src.jobs.queue import QUEUE_KEY, _IDEMPOTENCY_KEY_PREFIX, enqueue_analysis_job


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
    async def test_calls_lpush_with_queue_key(self):
        redis = AsyncMock()
        redis.set.return_value = True
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1,
            telegram_message_id=1,
        )
        await enqueue_analysis_job(redis, job)
        redis.lpush.assert_awaited_once()
        call_args = redis.lpush.call_args[0]
        assert call_args[0] == QUEUE_KEY

    @pytest.mark.asyncio
    async def test_enqueued_payload_is_valid_json(self):
        redis = AsyncMock()
        redis.set.return_value = True
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/55",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=99,
            telegram_message_id=10,
        )
        await enqueue_analysis_job(redis, job)
        payload = redis.lpush.call_args[0][1]
        data = json.loads(payload)
        assert data["source_url"] == "https://www.airbnb.com/rooms/55"
        assert data["telegram_chat_id"] == 99
        assert data["telegram_message_id"] == 10
        assert data["provider"] == "airbnb"

    @pytest.mark.asyncio
    async def test_enqueued_payload_roundtrips_to_analysis_job(self):
        redis = AsyncMock()
        redis.set.return_value = True
        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/7",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=2,
            telegram_message_id=3,
        )
        await enqueue_analysis_job(redis, job)
        payload = redis.lpush.call_args[0][1]
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
    async def test_sets_idempotency_key_with_nx_and_ex(self):
        redis = AsyncMock()
        redis.set.return_value = True
        await enqueue_analysis_job(redis, self._make_job())
        redis.set.assert_awaited_once()
        call_kwargs = redis.set.call_args[1]
        assert call_kwargs.get("nx") is True
        assert "ex" in call_kwargs

    @pytest.mark.asyncio
    async def test_idempotency_key_includes_chat_and_message_ids(self):
        redis = AsyncMock()
        redis.set.return_value = True
        await enqueue_analysis_job(redis, self._make_job(chat_id=42, message_id=99))
        key = redis.set.call_args[0][0]
        assert _IDEMPOTENCY_KEY_PREFIX in key
        assert "42" in key
        assert "99" in key

    @pytest.mark.asyncio
    async def test_returns_true_when_newly_enqueued(self):
        redis = AsyncMock()
        redis.set.return_value = True
        result = await enqueue_analysis_job(redis, self._make_job())
        assert result is True
        redis.lpush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_false_and_skips_lpush_when_already_enqueued(self):
        """SET NX returns None when the key already exists — lpush must be skipped."""
        redis = AsyncMock()
        redis.set.return_value = None  # Redis returns None when NX key already set
        result = await enqueue_analysis_job(redis, self._make_job())
        assert result is False
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

    @patch("src.telegram.router.enqueue_analysis_job", new_callable=AsyncMock)
    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_enqueue_called_when_redis_available(self, mock_send, mock_enqueue):
        from fastapi.testclient import TestClient

        from src.app.main import create_app

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
        """Without a Redis connection, enqueue is silently skipped."""
        from fastapi.testclient import TestClient

        from src.app.main import create_app

        app = create_app(settings=_test_settings())
        # app.state.redis is None by default (no lifespan run in TestClient without context)

        client = TestClient(app)
        response = client.post("/telegram/webhook", json=self._airbnb_payload())
        assert response.status_code == 200
        mock_enqueue.assert_not_awaited()

    @patch("src.telegram.router.enqueue_analysis_job", new_callable=AsyncMock)
    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_warning_logged_when_redis_is_none(self, mock_send, mock_enqueue, caplog):
        """A WARNING must be emitted when Redis is unavailable and enqueue is skipped."""
        from fastapi.testclient import TestClient

        from src.app.main import create_app

        app = create_app(settings=_test_settings())
        # app.state.redis is None by default

        client = TestClient(app)
        with caplog.at_level(logging.WARNING, logger="src.telegram.router"):
            response = client.post("/telegram/webhook", json=self._airbnb_payload())

        assert response.status_code == 200
        assert any("Redis" in r.message or "redis" in r.message.lower() for r in caplog.records)
        mock_enqueue.assert_not_awaited()

    @patch("src.telegram.router.enqueue_analysis_job", new_callable=AsyncMock)
    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_enqueue_not_called_for_unsupported_url(self, mock_send, mock_enqueue):
        from fastapi.testclient import TestClient

        from src.app.main import create_app

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
