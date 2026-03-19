"""Internationalisation helpers for flatscanner bot output."""

from src.i18n.catalog import get_string
from src.i18n.types import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, Language

__all__ = [
    "Language",
    "DEFAULT_LANGUAGE",
    "SUPPORTED_LANGUAGES",
    "get_string",
]
