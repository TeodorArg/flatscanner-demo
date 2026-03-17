"""Tests for the Telegram analysis message formatter."""

from __future__ import annotations

from src.analysis.result import AnalysisResult, PriceVerdict
from src.domain.listing import ListingProvider, NormalizedListing
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
        "summary": "A charming place to stay.",
        "strengths": ["Great location", "Superhost"],
        "risks": ["Small space", "Steep cleaning fee"],
        "price_verdict": PriceVerdict.FAIR,
        "price_explanation": "Price is in line with similar studios.",
    }
    base.update(overrides)
    return AnalysisResult(**base)


class TestMessageStructure:
    def test_title_appears_at_start(self):
        msg = format_analysis_message(_listing(), _result())
        assert msg.startswith("Cozy Studio in Paris")

    def test_summary_present(self):
        msg = format_analysis_message(_listing(), _result())
        assert "A charming place to stay." in msg

    def test_strengths_section_present(self):
        msg = format_analysis_message(_listing(), _result())
        assert "Strengths:" in msg
        assert "- Great location" in msg
        assert "- Superhost" in msg

    def test_risks_section_present(self):
        msg = format_analysis_message(_listing(), _result())
        assert "Risks:" in msg
        assert "- Small space" in msg
        assert "- Steep cleaning fee" in msg

    def test_price_section_with_explanation(self):
        msg = format_analysis_message(_listing(), _result())
        assert "Price: Fair - Price is in line with similar studios." in msg

    def test_sections_separated_by_blank_lines(self):
        msg = format_analysis_message(_listing(), _result())
        assert "\n\n" in msg


class TestVerdictWording:
    def test_fair_verdict(self):
        msg = format_analysis_message(_listing(), _result(price_verdict=PriceVerdict.FAIR))
        assert "Price: Fair" in msg

    def test_overpriced_verdict(self):
        msg = format_analysis_message(
            _listing(), _result(price_verdict=PriceVerdict.OVERPRICED)
        )
        assert "Price: Overpriced" in msg

    def test_underpriced_verdict(self):
        msg = format_analysis_message(
            _listing(), _result(price_verdict=PriceVerdict.UNDERPRICED)
        )
        assert "Price: Underpriced" in msg

    def test_unknown_verdict(self):
        msg = format_analysis_message(
            _listing(), _result(price_verdict=PriceVerdict.UNKNOWN)
        )
        assert "Price: Unknown" in msg


class TestOmissionAndFallback:
    def test_empty_strengths_omits_section(self):
        msg = format_analysis_message(_listing(), _result(strengths=[]))
        assert "Strengths:" not in msg

    def test_empty_risks_omits_section(self):
        msg = format_analysis_message(_listing(), _result(risks=[]))
        assert "Risks:" not in msg

    def test_both_empty_message_still_valid(self):
        msg = format_analysis_message(_listing(), _result(strengths=[], risks=[]))
        assert "Cozy Studio in Paris" in msg
        assert "A charming place to stay." in msg
        assert "Strengths:" not in msg
        assert "Risks:" not in msg
        assert "Price:" in msg

    def test_no_price_explanation_omits_separator(self):
        msg = format_analysis_message(
            _listing(),
            _result(price_explanation="", strengths=[], risks=[]),
        )
        price_line = msg.splitlines()[-1]
        assert price_line == "Price: Fair"
        assert " - " not in price_line

    def test_single_strength_bullet(self):
        msg = format_analysis_message(_listing(), _result(strengths=["Only one"]))
        assert "- Only one" in msg

    def test_single_risk_bullet(self):
        msg = format_analysis_message(_listing(), _result(risks=["Only risk"]))
        assert "- Only risk" in msg


class TestLengthGuard:
    def test_short_message_not_truncated(self):
        msg = format_analysis_message(_listing(), _result())
        assert _TRUNCATION_SUFFIX not in msg

    def test_long_message_truncated_with_notice(self):
        long_summary = "x" * (_TELEGRAM_MAX_CHARS + 500)
        result = _result(summary=long_summary)
        msg = format_analysis_message(_listing(), result)
        assert len(msg) <= _TELEGRAM_MAX_CHARS
        assert msg.endswith(_TRUNCATION_SUFFIX)

    def test_truncated_message_exactly_at_limit(self):
        long_summary = "y" * (_TELEGRAM_MAX_CHARS + 1000)
        result = _result(summary=long_summary)
        msg = format_analysis_message(_listing(), result)
        assert len(msg) == _TELEGRAM_MAX_CHARS

    def test_message_at_exact_limit_not_truncated(self):
        from src.telegram.formatter import _guard_length

        at_limit = "a" * _TELEGRAM_MAX_CHARS
        assert _guard_length(at_limit) == at_limit

    def test_message_one_over_limit_is_truncated(self):
        from src.telegram.formatter import _guard_length

        over_limit = "b" * (_TELEGRAM_MAX_CHARS + 1)
        result = _guard_length(over_limit)
        assert len(result) == _TELEGRAM_MAX_CHARS
        assert result.endswith(_TRUNCATION_SUFFIX)
