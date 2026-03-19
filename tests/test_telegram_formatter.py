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
        assert "Плюсы:" in msg
        assert "- Great location" in msg
        assert "- Superhost" in msg

    def test_risks_section_present(self):
        msg = format_analysis_message(_listing(), _result())
        assert "Риски:" in msg
        assert "- Small space" in msg
        assert "- Steep cleaning fee" in msg

    def test_price_section_with_explanation(self):
        msg = format_analysis_message(_listing(), _result())
        assert "Цена: Справедливо - Price is in line with similar studios." in msg

    def test_sections_separated_by_blank_lines(self):
        msg = format_analysis_message(_listing(), _result())
        assert "\n\n" in msg


class TestVerdictWording:
    def test_fair_verdict(self):
        msg = format_analysis_message(_listing(), _result(price_verdict=PriceVerdict.FAIR))
        assert "Цена: Справедливо" in msg

    def test_overpriced_verdict(self):
        msg = format_analysis_message(
            _listing(), _result(price_verdict=PriceVerdict.OVERPRICED)
        )
        assert "Цена: Завышено" in msg

    def test_underpriced_verdict(self):
        msg = format_analysis_message(
            _listing(), _result(price_verdict=PriceVerdict.UNDERPRICED)
        )
        assert "Цена: Занижено" in msg

    def test_unknown_verdict(self):
        msg = format_analysis_message(
            _listing(), _result(price_verdict=PriceVerdict.UNKNOWN)
        )
        assert "Цена: Неясно" in msg


class TestOmissionAndFallback:
    def test_empty_strengths_omits_section(self):
        msg = format_analysis_message(_listing(), _result(strengths=[]))
        assert "Плюсы:" not in msg

    def test_empty_risks_omits_section(self):
        msg = format_analysis_message(_listing(), _result(risks=[]))
        assert "Риски:" not in msg

    def test_both_empty_message_still_valid(self):
        msg = format_analysis_message(_listing(), _result(strengths=[], risks=[]))
        assert "Cozy Studio in Paris" in msg
        assert "A charming place to stay." in msg
        assert "Плюсы:" not in msg
        assert "Риски:" not in msg
        assert "Цена:" in msg

    def test_no_price_explanation_omits_separator(self):
        msg = format_analysis_message(
            _listing(),
            _result(price_explanation="", strengths=[], risks=[]),
        )
        price_line = msg.splitlines()[-1]
        assert price_line == "Цена: Справедливо"
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


# ---------------------------------------------------------------------------
# Multilingual formatter output
# ---------------------------------------------------------------------------


class TestFormatterEnglishOutput:
    """English output uses English labels."""

    def test_strengths_label_is_english(self):
        msg = format_analysis_message(_listing(), _result(), Language.EN)
        assert "Pros:" in msg
        assert "Плюсы:" not in msg

    def test_risks_label_is_english(self):
        msg = format_analysis_message(_listing(), _result(), Language.EN)
        assert "Risks:" in msg
        assert "Риски:" not in msg

    def test_price_label_is_english(self):
        msg = format_analysis_message(_listing(), _result(), Language.EN)
        assert "Price:" in msg
        assert "Цена:" not in msg

    def test_fair_verdict_is_english(self):
        msg = format_analysis_message(_listing(), _result(price_verdict=PriceVerdict.FAIR), Language.EN)
        assert "Fair" in msg

    def test_overpriced_verdict_is_english(self):
        msg = format_analysis_message(_listing(), _result(price_verdict=PriceVerdict.OVERPRICED), Language.EN)
        assert "Overpriced" in msg

    def test_underpriced_verdict_is_english(self):
        msg = format_analysis_message(_listing(), _result(price_verdict=PriceVerdict.UNDERPRICED), Language.EN)
        assert "Underpriced" in msg

    def test_unknown_verdict_is_english(self):
        msg = format_analysis_message(_listing(), _result(price_verdict=PriceVerdict.UNKNOWN), Language.EN)
        assert "Unknown" in msg

    def test_truncation_suffix_is_english(self):
        from src.telegram.formatter import _guard_length

        over_limit = "c" * (_TELEGRAM_MAX_CHARS + 1)
        result = _guard_length(over_limit, Language.EN)
        assert result.endswith("\n\n[Message truncated]")
        assert "[Сообщение обрезано]" not in result


class TestFormatterSpanishOutput:
    """Spanish output uses Spanish labels."""

    def test_strengths_label_is_spanish(self):
        msg = format_analysis_message(_listing(), _result(), Language.ES)
        assert "Ventajas:" in msg
        assert "Плюсы:" not in msg

    def test_risks_label_is_spanish(self):
        msg = format_analysis_message(_listing(), _result(), Language.ES)
        assert "Riesgos:" in msg
        assert "Риски:" not in msg

    def test_price_label_is_spanish(self):
        msg = format_analysis_message(_listing(), _result(), Language.ES)
        assert "Precio:" in msg
        assert "Цена:" not in msg

    def test_fair_verdict_is_spanish(self):
        msg = format_analysis_message(_listing(), _result(price_verdict=PriceVerdict.FAIR), Language.ES)
        assert "Justo" in msg

    def test_overpriced_verdict_is_spanish(self):
        msg = format_analysis_message(_listing(), _result(price_verdict=PriceVerdict.OVERPRICED), Language.ES)
        assert "Excesivo" in msg

    def test_truncation_suffix_is_spanish(self):
        from src.telegram.formatter import _guard_length

        over_limit = "d" * (_TELEGRAM_MAX_CHARS + 1)
        result = _guard_length(over_limit, Language.ES)
        assert result.endswith("\n\n[Mensaje truncado]")


class TestFormatterRussianDefault:
    """Russian remains the default when no language is passed."""

    def test_default_uses_russian_labels(self):
        msg = format_analysis_message(_listing(), _result())
        assert "Плюсы:" in msg
        assert "Риски:" in msg
        assert "Цена:" in msg

    def test_explicit_ru_uses_russian_labels(self):
        msg = format_analysis_message(_listing(), _result(), Language.RU)
        assert "Плюсы:" in msg

    def test_all_languages_produce_non_empty_output(self):
        listing = _listing()
        result = _result()
        for lang in Language:
            msg = format_analysis_message(listing, result, lang)
            assert msg, f"Empty output for language {lang}"

    def test_all_languages_include_listing_title(self):
        listing = _listing()
        result = _result()
        for lang in Language:
            msg = format_analysis_message(listing, result, lang)
            assert "Cozy Studio in Paris" in msg, f"Title missing for language {lang}"
