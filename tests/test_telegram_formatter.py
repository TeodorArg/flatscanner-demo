"""Tests for the Telegram analysis message formatter."""

from __future__ import annotations

from src.analysis.result import AnalysisResult, PriceVerdict
from src.domain.listing import ListingProvider, NormalizedListing
from src.i18n.types import Language
from src.telegram.formatter import (
    _TELEGRAM_MAX_CHARS,
    _TRUNCATION_SUFFIX,
    format_analysis_message,
)


def _listing(**overrides) -> NormalizedListing:
    base = {
        "provider": ListingProvider.AIRBNB,
        "source_url": "https://www.airbnb.com/rooms/12345",
        "source_id": "12345",
        "title": "Cozy Studio in Paris",
    }
    base.update(overrides)
    return NormalizedListing(**base)


def _result(**overrides) -> AnalysisResult:
    base = {
        "display_title": "Cozy Studio in Paris",
        "summary": "A charming place to stay.",
        "strengths": ["Great location", "Superhost"],
        "risks": ["Small space", "Steep cleaning fee"],
        "price_verdict": PriceVerdict.FAIR,
        "price_explanation": "Price is in line with similar studios.",
    }
    base.update(overrides)
    return AnalysisResult(**base)


class TestMessageStructure:
    def test_title_appears_at_start_in_bold(self):
        msg = format_analysis_message(_listing(), _result(), Language.EN)
        assert msg.startswith("<b>Cozy Studio in Paris</b>")

    def test_display_title_overrides_listing_title(self):
        msg = format_analysis_message(
            _listing(title="Original Provider Title"),
            _result(display_title="Localized Render Title"),
            Language.EN,
        )
        assert msg.startswith("<b>Localized Render Title</b>")
        assert "Original Provider Title" not in msg.split("\n\n", 1)[0]

    def test_summary_present_and_escaped(self):
        msg = format_analysis_message(
            _listing(),
            _result(summary="A <bright> & charming place."),
            Language.EN,
        )
        assert "A &lt;bright&gt; &amp; charming place." in msg

    def test_strengths_section_present_in_bold(self):
        msg = format_analysis_message(_listing(), _result(), Language.EN)
        assert "<b>Pros:</b>" in msg
        assert "- Great location" in msg
        assert "- Superhost" in msg

    def test_risks_section_present_in_bold(self):
        msg = format_analysis_message(_listing(), _result(), Language.EN)
        assert "<b>Risks:</b>" in msg
        assert "- Small space" in msg
        assert "- Steep cleaning fee" in msg

    def test_price_section_with_explanation_in_bold(self):
        msg = format_analysis_message(_listing(), _result(), Language.EN)
        assert "<b>Price: Fair</b> - Price is in line with similar studios." in msg

    def test_sections_separated_by_blank_lines(self):
        msg = format_analysis_message(_listing(), _result(), Language.EN)
        assert "\n\n" in msg


class TestVerdictWording:
    def test_fair_verdict(self):
        msg = format_analysis_message(_listing(), _result(price_verdict=PriceVerdict.FAIR), Language.EN)
        assert "<b>Price: Fair</b>" in msg

    def test_overpriced_verdict(self):
        msg = format_analysis_message(
            _listing(), _result(price_verdict=PriceVerdict.OVERPRICED), Language.EN
        )
        assert "<b>Price: Overpriced</b>" in msg

    def test_underpriced_verdict(self):
        msg = format_analysis_message(
            _listing(), _result(price_verdict=PriceVerdict.UNDERPRICED), Language.EN
        )
        assert "<b>Price: Underpriced</b>" in msg

    def test_unknown_verdict(self):
        msg = format_analysis_message(
            _listing(), _result(price_verdict=PriceVerdict.UNKNOWN), Language.EN
        )
        assert "<b>Price: Unknown</b>" in msg


class TestOmissionAndFallback:
    def test_empty_strengths_omits_section(self):
        msg = format_analysis_message(_listing(), _result(strengths=[]), Language.EN)
        assert "<b>Pros:</b>" not in msg

    def test_empty_risks_omits_section(self):
        msg = format_analysis_message(_listing(), _result(risks=[]), Language.EN)
        assert "<b>Risks:</b>" not in msg

    def test_both_empty_message_still_valid(self):
        msg = format_analysis_message(_listing(), _result(strengths=[], risks=[]), Language.EN)
        assert "<b>Cozy Studio in Paris</b>" in msg
        assert "A charming place to stay." in msg
        assert "<b>Pros:</b>" not in msg
        assert "<b>Risks:</b>" not in msg
        assert "<b>Price: Fair</b>" in msg

    def test_no_price_explanation_omits_separator(self):
        msg = format_analysis_message(
            _listing(),
            _result(price_explanation="", strengths=[], risks=[]),
            Language.EN,
        )
        price_line = msg.splitlines()[-1]
        assert price_line == "<b>Price: Fair</b>"
        assert " - " not in price_line


class TestLengthGuard:
    def test_short_message_not_truncated(self):
        msg = format_analysis_message(_listing(), _result(), Language.EN)
        assert _TRUNCATION_SUFFIX not in msg

    def test_long_message_truncated_with_notice(self):
        long_summary = "x" * (_TELEGRAM_MAX_CHARS + 500)
        result = _result(summary=long_summary)
        msg = format_analysis_message(_listing(), result, Language.EN)
        assert len(msg) <= _TELEGRAM_MAX_CHARS
        assert msg.endswith("\n\n[Message truncated]")

    def test_truncated_message_exactly_at_limit(self):
        long_summary = "y" * (_TELEGRAM_MAX_CHARS + 1000)
        result = _result(summary=long_summary)
        msg = format_analysis_message(_listing(), result, Language.EN)
        assert len(msg) == _TELEGRAM_MAX_CHARS


class TestMultilingualOutput:
    def test_english_labels_are_bold(self):
        msg = format_analysis_message(_listing(), _result(), Language.EN)
        assert "<b>Pros:</b>" in msg
        assert "<b>Risks:</b>" in msg
        assert "<b>Price: Fair</b>" in msg

    def test_spanish_labels_are_bold(self):
        msg = format_analysis_message(_listing(), _result(), Language.ES)
        assert "<b>Ventajas:</b>" in msg
        assert "<b>Riesgos:</b>" in msg
        assert "<b>Precio: Justo</b>" in msg

    def test_russian_default_still_non_empty(self):
        msg = format_analysis_message(_listing(), _result())
        assert msg
        assert msg.startswith("<b>")
