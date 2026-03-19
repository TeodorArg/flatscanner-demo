"""Redis-backed repository for Telegram chat language preferences.

Language preferences are stored in Redis under keys of the form
``flatscanner:chat_lang:<chat_id>``.  The value is the ``Language`` enum
string (e.g. ``"ru"``).

A chat with no key stored defaults to ``DEFAULT_LANGUAGE`` (Russian) at
read time.  Keys have no TTL — preferences persist until overwritten.

The ``TelegramChatPreferenceRow`` ORM model in ``storage.models`` mirrors
this data in PostgreSQL for durability and audit purposes; that persistence
path is wired in a later slice.
"""

from __future__ import annotations

from redis.asyncio import Redis

from src.i18n.types import DEFAULT_LANGUAGE, Language

_KEY_PREFIX = "flatscanner:chat_lang"


def _key(chat_id: int) -> str:
    return f"{_KEY_PREFIX}:{chat_id}"


async def get_chat_language(redis: Redis, chat_id: int) -> Language:
    """Return the persisted language for *chat_id*, or ``DEFAULT_LANGUAGE``.

    Parameters
    ----------
    redis:
        Async Redis client.
    chat_id:
        Telegram chat identifier.
    """
    value = await redis.get(_key(chat_id))
    if value is None:
        return DEFAULT_LANGUAGE
    try:
        return Language(value)
    except ValueError:
        return DEFAULT_LANGUAGE


async def set_chat_language(redis: Redis, chat_id: int, language: Language) -> None:
    """Persist *language* as the preference for *chat_id*.

    Parameters
    ----------
    redis:
        Async Redis client.
    chat_id:
        Telegram chat identifier.
    language:
        The language to store.
    """
    await redis.set(_key(chat_id), language.value)
