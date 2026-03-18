"""Telegram message formatter for listing analysis results.

Accepts a NormalizedListing and AnalysisResult and returns a
Telegram-safe plain-text message. The output is intentionally
short and deterministic so it stays within Telegram's 4096-character
message limit.
"""

from __future__ import annotations

from src.analysis.result import AnalysisResult, PriceVerdict
from src.domain.listing import NormalizedListing

# Telegram hard limit for a single message is 4096 characters.
# This formatter keeps output short and ASCII-friendly, so a simple character
# count is a practical guard against oversize messages.
_TELEGRAM_MAX_CHARS = 4096
_TRUNCATION_SUFFIX = "\n\n[Сообщение обрезано]"


_VERDICT_LABEL: dict[PriceVerdict, str] = {
    PriceVerdict.FAIR: "Справедливо",
    PriceVerdict.OVERPRICED: "Завышено",
    PriceVerdict.UNDERPRICED: "Занижено",
    PriceVerdict.UNKNOWN: "Неясно",
}


def format_analysis_message(
    listing: NormalizedListing,
    result: AnalysisResult,
) -> str:
    """Return a formatted plain-text message suitable for Telegram.

    Sections included:
    - Listing title (header)
    - Summary paragraph
    - Strengths bullet list (omitted when empty)
    - Risks bullet list (omitted when empty)
    - Price fairness verdict and explanation

    The message is truncated with a notice if it would exceed
    ``_TELEGRAM_MAX_CHARS`` characters.
    """
    parts: list[str] = []

    parts.append(listing.title)
    parts.append(result.summary)

    if result.strengths:
        lines = ["Плюсы:"] + [f"- {strength}" for strength in result.strengths]
        parts.append("\n".join(lines))

    if result.risks:
        lines = ["Риски:"] + [f"- {risk}" for risk in result.risks]
        parts.append("\n".join(lines))

    verdict_label = _VERDICT_LABEL.get(result.price_verdict, "Неясно")
    if result.price_explanation:
        price_line = f"Цена: {verdict_label} - {result.price_explanation}"
    else:
        price_line = f"Цена: {verdict_label}"
    parts.append(price_line)

    message = "\n\n".join(parts)
    return _guard_length(message)


def _guard_length(message: str) -> str:
    """Truncate message and append a notice if it exceeds the Telegram limit."""
    if len(message) <= _TELEGRAM_MAX_CHARS:
        return message
    cut = _TELEGRAM_MAX_CHARS - len(_TRUNCATION_SUFFIX)
    return message[:cut] + _TRUNCATION_SUFFIX
