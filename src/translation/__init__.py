"""On-demand translation of AI-generated freeform analysis blocks.

Translated output is ephemeral — it is never persisted.  Canonical
analysis results stay in English; this layer translates them just before
Telegram formatting.
"""

from src.translation.service import TranslationError, TranslationService

__all__ = ["TranslationService", "TranslationError"]
