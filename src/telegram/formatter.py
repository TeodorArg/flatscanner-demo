"""Telegram message formatter for listing analysis results.

Accepts a NormalizedListing, an already-translated AnalysisResult, and a
Language, and returns a Telegram-safe plain-text message.  The formatter
is intentionally pure: it never performs translation itself.  All section
labels come from the i18n catalog, so new output block types can be added
without touching catalog keys for existing blocks.

Output is kept short and deterministic to stay within Telegram's 4096-
character message limit.
"""

from __future__ import annotations

from src.analysis.result import AnalysisResult, PriceVerdict
from src.domain.listing import NormalizedListing
from src.i18n.catalog import get_string
from src.i18n.types import DEFAULT_LANGUAGE, Language

# Telegram hard limit for a single message is 4096 characters.
# This formatter keeps output short and ASCII-friendly, so a simple character
# count is a practical guard against oversize messages.
_TELEGRAM_MAX_CHARS = 4096

# Kept as a module-level constant so existing tests that import it directly
# remain stable.  Its value matches the Russian catalog entry.
_TRUNCATION_SUFFIX = "\n\n[Сообщение обрезано]"

# Map PriceVerdict enum values to their i18n catalog keys.
_VERDICT_KEY: dict[PriceVerdict, str] = {
    PriceVerdict.FAIR: "fmt.verdict.fair",
    PriceVerdict.OVERPRICED: "fmt.verdict.overpriced",
    PriceVerdict.UNDERPRICED: "fmt.verdict.underpriced",
    PriceVerdict.UNKNOWN: "fmt.verdict.unknown",
}


def format_analysis_message(
    listing: NormalizedListing,
    result: AnalysisResult,
    language: Language = DEFAULT_LANGUAGE,
) -> str:
    """Return a formatted plain-text message suitable for Telegram.

    The formatter is pure: *result* must already contain translated freeform
    blocks for non-English languages.  All section labels are looked up from
    the i18n catalog using *language*.

    Sections included:
    - Localized display title (header)
    - Summary paragraph
    - Strengths bullet list (omitted when empty)
    - Risks bullet list (omitted when empty)
    - Price fairness verdict and explanation

    The message is truncated with a localized notice if it would exceed
    ``_TELEGRAM_MAX_CHARS`` characters.

    Parameters
    ----------
    listing:
        Provider-agnostic normalized listing. Used as a fallback source for
        the header when ``result.display_title`` is empty.
    result:
        Already-translated analysis result.
    language:
        Language for section labels and the truncation notice.
        Defaults to ``DEFAULT_LANGUAGE`` (Russian).
    """
    parts: list[str] = []

    header = result.display_title or listing.title
    parts.append(header)
    parts.append(result.summary)

    if result.strengths:
        label = get_string("fmt.strengths_label", language)
        lines = [label] + [f"- {strength}" for strength in result.strengths]
        parts.append("\n".join(lines))

    if result.risks:
        label = get_string("fmt.risks_label", language)
        lines = [label] + [f"- {risk}" for risk in result.risks]
        parts.append("\n".join(lines))

    price_label = get_string("fmt.price_label", language)
    verdict_key = _VERDICT_KEY.get(result.price_verdict, "fmt.verdict.unknown")
    verdict_label = get_string(verdict_key, language)
    if result.price_explanation:
        price_line = f"{price_label} {verdict_label} - {result.price_explanation}"
    else:
        price_line = f"{price_label} {verdict_label}"
    parts.append(price_line)

    message = "\n\n".join(parts)
    return _guard_length(message, language)


def _guard_length(message: str, language: Language = DEFAULT_LANGUAGE) -> str:
    """Truncate message and append a localized notice if it exceeds the Telegram limit."""
    if len(message) <= _TELEGRAM_MAX_CHARS:
        return message
    suffix = get_string("fmt.truncated", language)
    cut = _TELEGRAM_MAX_CHARS - len(suffix)
    return message[:cut] + suffix
