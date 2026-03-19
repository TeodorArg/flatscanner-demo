"""Language enum and related constants for the i18n layer."""

from __future__ import annotations

from enum import Enum


class Language(str, Enum):
    """Supported user-facing output languages."""

    RU = "ru"
    EN = "en"
    ES = "es"


# Russian is the default language for new Telegram chats.
DEFAULT_LANGUAGE: Language = Language.RU

SUPPORTED_LANGUAGES: frozenset[Language] = frozenset(Language)
