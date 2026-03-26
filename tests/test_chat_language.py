"""Tests for Telegram chat language preference persistence and job snapshotting."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.i18n.types import DEFAULT_LANGUAGE, Language
from src.storage.chat_preferences import (
    _KEY_PREFIX,
    get_chat_language,
    set_chat_language,
)


# ---------------------------------------------------------------------------
# get_chat_language
# ---------------------------------------------------------------------------


class TestGetChatLanguage:
    @pytest.mark.asyncio
    async def test_returns_default_when_no_key(self):
        redis = AsyncMock()
        redis.get.return_value = None
        result = await get_chat_language(redis, chat_id=1001)
        assert result == DEFAULT_LANGUAGE
        assert result == Language.RU

    @pytest.mark.asyncio
    async def test_returns_stored_language(self):
        redis = AsyncMock()
        redis.get.return_value = "en"
        result = await get_chat_language(redis, chat_id=1001)
        assert result == Language.EN

    @pytest.mark.asyncio
    async def test_decodes_bytes_from_redis(self):
        redis = AsyncMock()
        redis.get.return_value = b"en"
        result = await get_chat_language(redis, chat_id=1001)
        assert result == Language.EN

    @pytest.mark.asyncio
    async def test_returns_spanish_when_stored(self):
        redis = AsyncMock()
        redis.get.return_value = "es"
        result = await get_chat_language(redis, chat_id=42)
        assert result == Language.ES

    @pytest.mark.asyncio
    async def test_returns_default_for_invalid_stored_value(self):
        """Corrupt or outdated value in Redis must not crash; fall back to default."""
        redis = AsyncMock()
        redis.get.return_value = "xx"
        result = await get_chat_language(redis, chat_id=1001)
        assert result == DEFAULT_LANGUAGE

    @pytest.mark.asyncio
    async def test_uses_correct_redis_key(self):
        redis = AsyncMock()
        redis.get.return_value = None
        await get_chat_language(redis, chat_id=9999)
        redis.get.assert_awaited_once_with(f"{_KEY_PREFIX}:9999")


# ---------------------------------------------------------------------------
# set_chat_language
# ---------------------------------------------------------------------------


class TestSetChatLanguage:
    @pytest.mark.asyncio
    async def test_sets_language_value_in_redis(self):
        redis = AsyncMock()
        await set_chat_language(redis, chat_id=1001, language=Language.EN)
        redis.set.assert_awaited_once_with(f"{_KEY_PREFIX}:1001", "en")

    @pytest.mark.asyncio
    async def test_set_then_get_roundtrip(self):
        stored: dict[str, str] = {}

        async def fake_set(key: str, value: str) -> None:
            stored[key] = value

        async def fake_get(key: str) -> str | None:
            return stored.get(key)

        redis = AsyncMock()
        redis.set.side_effect = fake_set
        redis.get.side_effect = fake_get

        await set_chat_language(redis, chat_id=7, language=Language.ES)
        result = await get_chat_language(redis, chat_id=7)
        assert result == Language.ES

    @pytest.mark.asyncio
    async def test_overwrite_changes_language(self):
        stored: dict[str, str] = {}

        async def fake_set(key: str, value: str) -> None:
            stored[key] = value

        async def fake_get(key: str) -> str | None:
            return stored.get(key)

        redis = AsyncMock()
        redis.set.side_effect = fake_set
        redis.get.side_effect = fake_get

        await set_chat_language(redis, chat_id=5, language=Language.RU)
        await set_chat_language(redis, chat_id=5, language=Language.EN)
        result = await get_chat_language(redis, chat_id=5)
        assert result == Language.EN


# ---------------------------------------------------------------------------
# Router integration: language snapshotted onto AnalysisJob
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


class TestRouterLanguageSnapshot:
    """The router must read the chat's language preference and snapshot it onto the job."""

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
    @patch("src.telegram.router.send_message_return_id", new_callable=AsyncMock)
    @patch(
        "src.telegram.router.get_chat_language",
        new_callable=AsyncMock,
    )
    def test_job_carries_default_language_when_no_preference(
        self, mock_get_lang, mock_send_id, mock_enqueue
    ):
        from fastapi.testclient import TestClient

        from src.app.main import create_app
        from src.domain.listing import AnalysisJob

        mock_get_lang.return_value = Language.RU
        mock_send_id.return_value = 999
        mock_enqueue.return_value = True

        app = create_app(settings=_test_settings())
        app.state.redis = MagicMock()
        client = TestClient(app, raise_server_exceptions=True)
        response = client.post("/telegram/webhook", json=self._airbnb_payload())

        assert response.status_code == 200
        mock_enqueue.assert_awaited_once()
        job: AnalysisJob = mock_enqueue.call_args[0][1]
        assert job.language == Language.RU

    @patch("src.telegram.router.enqueue_analysis_job", new_callable=AsyncMock)
    @patch("src.telegram.router.send_message_return_id", new_callable=AsyncMock)
    @patch(
        "src.telegram.router.get_chat_language",
        new_callable=AsyncMock,
    )
    def test_job_carries_english_when_chat_preference_is_en(
        self, mock_get_lang, mock_send_id, mock_enqueue
    ):
        from fastapi.testclient import TestClient

        from src.app.main import create_app
        from src.domain.listing import AnalysisJob

        mock_get_lang.return_value = Language.EN
        mock_send_id.return_value = 999
        mock_enqueue.return_value = True

        app = create_app(settings=_test_settings())
        app.state.redis = MagicMock()
        client = TestClient(app, raise_server_exceptions=True)
        response = client.post("/telegram/webhook", json=self._airbnb_payload())

        assert response.status_code == 200
        mock_enqueue.assert_awaited_once()
        job: AnalysisJob = mock_enqueue.call_args[0][1]
        assert job.language == Language.EN

    @patch("src.telegram.router.enqueue_analysis_job", new_callable=AsyncMock)
    @patch("src.telegram.router.send_message_return_id", new_callable=AsyncMock)
    @patch(
        "src.telegram.router.get_chat_language",
        new_callable=AsyncMock,
    )
    def test_get_chat_language_called_with_correct_chat_id(
        self, mock_get_lang, mock_send_id, mock_enqueue
    ):
        from fastapi.testclient import TestClient

        from src.app.main import create_app

        mock_get_lang.return_value = Language.RU
        mock_send_id.return_value = 999
        mock_enqueue.return_value = True

        app = create_app(settings=_test_settings())
        mock_redis = MagicMock()
        app.state.redis = mock_redis
        client = TestClient(app, raise_server_exceptions=True)
        client.post("/telegram/webhook", json=self._airbnb_payload(chat_id=42))

        mock_get_lang.assert_awaited_once()
        args = mock_get_lang.call_args[0]
        assert args[0] is mock_redis
        assert args[1] == 42


# ---------------------------------------------------------------------------
# AnalysisJob: language field serialisation
# ---------------------------------------------------------------------------


class TestAnalysisJobLanguageField:
    def test_default_language_is_ru(self):
        from src.domain.listing import AnalysisJob, ListingProvider

        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1,
            telegram_message_id=1,
        )
        assert job.language == Language.RU

    def test_explicit_language_is_stored(self):
        from src.domain.listing import AnalysisJob, ListingProvider

        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1,
            telegram_message_id=1,
            language=Language.ES,
        )
        assert job.language == Language.ES

    def test_language_survives_json_roundtrip(self):
        from src.domain.listing import AnalysisJob, ListingProvider

        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1,
            telegram_message_id=1,
            language=Language.EN,
        )
        restored = AnalysisJob.model_validate_json(job.model_dump_json())
        assert restored.language == Language.EN

    def test_serialised_language_is_string_code(self):
        from src.domain.listing import AnalysisJob, ListingProvider

        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1,
            telegram_message_id=1,
            language=Language.RU,
        )
        data = json.loads(job.model_dump_json())
        assert data["language"] == "ru"
