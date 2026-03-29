"""Telegram message formatter for listing analysis results.

Accepts a NormalizedListing, an already-translated AnalysisResult, and a
Language, and returns a Telegram-safe HTML message. The formatter is
intentionally pure: it never performs translation itself. All section labels
come from the i18n catalog, so new output block types can be added without
touching catalog keys for existing blocks.

Output is kept short and deterministic to stay within Telegram's 4096-
character message limit.
"""

from __future__ import annotations

from html import escape

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
    """Return a formatted HTML message suitable for Telegram.

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
    parts.append(_bold(header))
    parts.append(_escape_text(result.summary))

    if result.strengths:
        label = get_string("fmt.strengths_label", language)
        lines = [_bold(label)] + [f"- {_escape_text(strength)}" for strength in result.strengths]
        parts.append("\n".join(lines))

    if result.risks:
        label = get_string("fmt.risks_label", language)
        lines = [_bold(label)] + [f"- {_escape_text(risk)}" for risk in result.risks]
        parts.append("\n".join(lines))

    reviews_section = _format_review_insights(result, language)
    if reviews_section:
        parts.append(reviews_section)

    stay_price_section = _format_stay_price(listing, language)
    if stay_price_section:
        parts.append(stay_price_section)

    price_label = get_string("fmt.price_label", language)
    verdict_key = _VERDICT_KEY.get(result.price_verdict, "fmt.verdict.unknown")
    verdict_label = get_string(verdict_key, language)
    price_heading = _bold(f"{price_label} {verdict_label}")
    if result.price_explanation:
        price_line = f"{price_heading} - {_escape_text(result.price_explanation)}"
    else:
        price_line = price_heading
    parts.append(price_line)

    message = "\n\n".join(parts)
    return _guard_length(message, language)


def _format_review_insights(result: AnalysisResult, language: Language) -> str:
    """Return a compact localized reviews section, or an empty string to omit it."""
    ri = result.review_insights
    if ri is None:
        return ""

    has_ai = bool(
        ri.overall_assessment
        or ri.critical_red_flags
        or ri.recurring_issues
        or ri.conflicts_or_disputes
        or ri.window_view_summary
    )
    has_metadata = ri.review_count is not None or ri.average_rating is not None

    if not has_ai and not has_metadata:
        return ""

    header = get_string("fmt.reviews_label", language)
    lines: list[str] = []

    # --- Metadata overview ---
    meta_parts: list[str] = []
    if ri.review_count is not None:
        meta_parts.append(str(ri.review_count))
    if ri.average_rating is not None:
        meta_parts.append(f"{ri.average_rating:.1f}★")
    if meta_parts:
        overview = _bold(header + " " + ", ".join(meta_parts))
    else:
        overview = _bold(header)
    lines.append(overview)

    # --- AI assessment ---
    if ri.overall_assessment:
        lines.append(_escape_text(ri.overall_assessment))

    # --- Critical red flags ---
    if ri.critical_red_flags:
        label = get_string("fmt.reviews_red_flags_label", language)
        lines.append(_bold(label))
        for flag in ri.critical_red_flags:
            lines.append(f"- {_escape_text(flag)}")

    # --- Recurring issues ---
    if ri.recurring_issues:
        label = get_string("fmt.reviews_recurring_label", language)
        lines.append(_bold(label))
        for issue in ri.recurring_issues:
            lines.append(f"- {_escape_text(issue)}")

    # --- Conflicts / disputes ---
    if ri.conflicts_or_disputes:
        label = get_string("fmt.reviews_disputes_label", language)
        lines.append(_bold(label))
        for dispute in ri.conflicts_or_disputes:
            lines.append(f"- {_escape_text(dispute)}")

    # --- Window view summary ---
    if ri.window_view_summary:
        window_label = get_string("fmt.reviews_window_label", language)
        lines.append(f"{_bold(window_label)} {_escape_text(ri.window_view_summary)}")

    return "\n".join(lines)


def _format_stay_price(listing: NormalizedListing, language: Language) -> str:
    """Return a compact stay-price block when the listing has dated stay details.

    Included when ``listing.price.period == 'stay'`` and at least check-in or
    stay_nights is present.  Returns an empty string otherwise so the caller
    can omit the section cleanly.
    """
    p = listing.price
    if p is None or p.period != "stay":
        return ""
    if not (p.check_in or p.stay_nights):
        return ""

    label = get_string("fmt.stay_price_label", language)
    lines: list[str] = []

    header_parts: list[str] = [label]
    if p.check_in and p.check_out:
        header_parts.append(f"{p.check_in} → {p.check_out}")
    if p.stay_nights is not None:
        nights_label = get_string("fmt.stay_nights_label", language)
        header_parts.append(f"{nights_label} {p.stay_nights}")
    lines.append(_bold(" ".join(header_parts)))

    total_line = _escape_text(f"{p.amount} {p.currency}")
    lines.append(total_line)

    if p.nightly_rate is not None:
        per_night_label = get_string("fmt.nightly_rate_label", language)
        lines.append(f"{_bold(per_night_label)} {_escape_text(f'{p.nightly_rate} {p.currency}')}")

    if p.cleaning_fee is not None:
        cleaning_label = get_string("fmt.cleaning_fee_label", language)
        lines.append(f"{_bold(cleaning_label)} {_escape_text(f'{p.cleaning_fee} {p.currency}')}")

    if p.service_fee is not None:
        service_label = get_string("fmt.service_fee_label", language)
        lines.append(f"{_bold(service_label)} {_escape_text(f'{p.service_fee} {p.currency}')}")

    return "\n".join(lines)


def _guard_length(message: str, language: Language = DEFAULT_LANGUAGE) -> str:
    """Truncate message and append a localized notice if it exceeds the Telegram limit."""
    if len(message) <= _TELEGRAM_MAX_CHARS:
        return message
    suffix = get_string("fmt.truncated", language)
    cut = _TELEGRAM_MAX_CHARS - len(suffix)
    return message[:cut] + suffix


def _escape_text(value: str) -> str:
    """Escape user-visible dynamic text for Telegram HTML parse mode."""
    return escape(value, quote=False)


def _bold(value: str) -> str:
    """Wrap text in Telegram HTML bold tags after escaping it."""
    return f"<b>{_escape_text(value)}</b>"
