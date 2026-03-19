"""Generalized chat settings model and Redis repository.

``ChatSettings`` is the single store for all per-chat bot configuration.
It currently holds only ``language``, but the model is structured to accept
additional preferences as the bot grows.

Storage delegates to the existing ``chat_preferences`` layer so the legacy
``/language`` command and the new menu-driven flow share the same Redis key
with no migration required.
"""

from __future__ import annotations

from pydantic import BaseModel
from redis.asyncio import Redis

from src.i18n.types import DEFAULT_LANGUAGE, Language
from src.storage.chat_preferences import get_chat_language, set_chat_language


class ChatSettings(BaseModel):
    language: Language = DEFAULT_LANGUAGE


async def get_chat_settings(redis: Redis, chat_id: int) -> ChatSettings:
    """Return persisted settings for *chat_id*, defaulting to ``DEFAULT_LANGUAGE``."""
    language = await get_chat_language(redis, chat_id)
    return ChatSettings(language=language)


async def save_chat_settings(redis: Redis, chat_id: int, settings: ChatSettings) -> None:
    """Persist *settings* for *chat_id*."""
    await set_chat_language(redis, chat_id, settings.language)
