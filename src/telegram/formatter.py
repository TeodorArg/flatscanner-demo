"""Telegram message formatter for listing analysis results.

Accepts a NormalizedListing and AnalysisResult and returns a
Telegram-safe plain-text message.  The output is intentionally
short and deterministic so it stays within Telegram's 4096-character
message limit.
"""

from __future__ import annotations

from src.analysis.result import AnalysisResult, PriceVerdict
from src.domain.listing import NormalizedListing

# Telegram hard limit for a single message is 4096 UTF-16 code units.
# We use a conservative byte budget to stay safely below it.
_TELEGRAM_MAX_CHARS = 4096
_TRUNCATION_SUFFIX = "\n\n[Message truncated]"


_VERDICT_LABEL: dict[PriceVerdict, str] = {
    PriceVerdict.FAIR: "Fair",
    PriceVerdict.OVERPRICED: "Overpriced",
    PriceVerdict.UNDERPRICED: "Underpriced",
    PriceVerdict.UNKNOWN: "Unknown",
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

    # Header
    parts.append(listing.title)

    # Summary
    parts.append(result.summary)

    # Strengths — omit section entirely when there are none
    if result.strengths:
        lines = ["Strengths:"] + [f"• {s}" for s in result.strengths]
        parts.append("\n".join(lines))

    # Risks — omit section entirely when there are none
    if result.risks:
        lines = ["Risks:"] + [f"• {r}" for r in result.risks]
        parts.append("\n".join(lines))

    # Price fairness
    verdict_label = _VERDICT_LABEL.get(result.price_verdict, "Unknown")
    if result.price_explanation:
        price_line = f"Price: {verdict_label} — {result.price_explanation}"
    else:
        price_line = f"Price: {verdict_label}"
    parts.append(price_line)

    message = "\n\n".join(parts)
    return _guard_length(message)


def _guard_length(message: str) -> str:
    """Truncate message and append a notice if it exceeds the Telegram limit."""
    if len(message) <= _TELEGRAM_MAX_CHARS:
        return message
    cut = _TELEGRAM_MAX_CHARS - len(_TRUNCATION_SUFFIX)
    return message[:cut] + _TRUNCATION_SUFFIX
