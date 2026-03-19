"""Tests for generalized ChatSettings persistence."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.i18n.types import DEFAULT_LANGUAGE, Language
from src.storage.chat_settings import ChatSettings, get_chat_settings, save_chat_settings


class TestChatSettingsModel:
    def test_default_language_is_ru(self):
        s = ChatSettings()
        assert s.language == DEFAULT_LANGUAGE
        assert s.language == Language.RU

    def test_explicit_language(self):
        s = ChatSettings(language=Language.EN)
        assert s.language == Language.EN

    def test_model_copy_update_language(self):
        original = ChatSettings(language=Language.RU)
        updated = original.model_copy(update={"language": Language.ES})
        assert updated.language == Language.ES
        assert original.language == Language.RU  # immutability


class TestGetChatSettings:
    @pytest.mark.asyncio
    async def test_returns_default_when_no_preference(self):
        redis = AsyncMock()
        redis.get.return_value = None
        settings = await get_chat_settings(redis, chat_id=1001)
        assert settings.language == DEFAULT_LANGUAGE

    @pytest.mark.asyncio
    async def test_returns_stored_language(self):
        redis = AsyncMock()
        redis.get.return_value = "en"
        settings = await get_chat_settings(redis, chat_id=1001)
        assert settings.language == Language.EN

    @pytest.mark.asyncio
    async def test_decodes_bytes_response(self):
        redis = AsyncMock()
        redis.get.return_value = b"es"
        settings = await get_chat_settings(redis, chat_id=42)
        assert settings.language == Language.ES

    @pytest.mark.asyncio
    async def test_returns_default_for_invalid_value(self):
        redis = AsyncMock()
        redis.get.return_value = "xx"
        settings = await get_chat_settings(redis, chat_id=1001)
        assert settings.language == DEFAULT_LANGUAGE

    @pytest.mark.asyncio
    async def test_returns_chat_settings_instance(self):
        redis = AsyncMock()
        redis.get.return_value = "ru"
        result = await get_chat_settings(redis, chat_id=1)
        assert isinstance(result, ChatSettings)


class TestSaveChatSettings:
    @pytest.mark.asyncio
    async def test_saves_language_to_redis(self):
        redis = AsyncMock()
        settings = ChatSettings(language=Language.EN)
        await save_chat_settings(redis, chat_id=1001, settings=settings)
        redis.set.assert_awaited_once()
        # Verify the value written is the language string
        args = redis.set.call_args[0]
        assert args[1] == "en"

    @pytest.mark.asyncio
    async def test_roundtrip_save_then_get(self):
        stored: dict[str, str] = {}

        async def fake_set(key: str, value: str) -> None:
            stored[key] = value

        async def fake_get(key: str) -> str | None:
            return stored.get(key)

        redis = AsyncMock()
        redis.set.side_effect = fake_set
        redis.get.side_effect = fake_get

        await save_chat_settings(redis, chat_id=7, settings=ChatSettings(language=Language.ES))
        result = await get_chat_settings(redis, chat_id=7)
        assert result.language == Language.ES

    @pytest.mark.asyncio
    async def test_overwrite_changes_persisted_language(self):
        stored: dict[str, str] = {}

        async def fake_set(key: str, value: str) -> None:
            stored[key] = value

        async def fake_get(key: str) -> str | None:
            return stored.get(key)

        redis = AsyncMock()
        redis.set.side_effect = fake_set
        redis.get.side_effect = fake_get

        await save_chat_settings(redis, chat_id=5, settings=ChatSettings(language=Language.RU))
        await save_chat_settings(redis, chat_id=5, settings=ChatSettings(language=Language.EN))
        result = await get_chat_settings(redis, chat_id=5)
        assert result.language == Language.EN
