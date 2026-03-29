"""Tests for the Telegram analysis message formatter."""

from __future__ import annotations

from src.analysis.result import AnalysisResult, PriceVerdict
from src.domain.listing import ListingProvider, NormalizedListing
from src.i18n.types import Language
from src.telegram.formatter import (
    _TELEGRAM_MAX_CHARS,
    _TRUNCATION_SUFFIX,
    _format_amenities,
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


class TestAmenitiesBlock:
    def test_amenities_present_when_non_empty(self):
        result = _result(amenities=["WiFi", "Kitchen", "Washer"])
        msg = format_analysis_message(_listing(), result, Language.EN)
        assert "<b>Amenities:</b>" in msg
        assert "- WiFi" in msg
        assert "- Kitchen" in msg
        assert "- Washer" in msg

    def test_amenities_omitted_when_empty(self):
        result = _result(amenities=[])
        msg = format_analysis_message(_listing(), result, Language.EN)
        assert "<b>Amenities:</b>" not in msg

    def test_amenities_default_omitted(self):
        # AnalysisResult.amenities defaults to [] so section must not appear
        msg = format_analysis_message(_listing(), _result(), Language.EN)
        assert "<b>Amenities:</b>" not in msg

    def test_amenities_all_items_rendered(self):
        amenities = [f"Feature{i}" for i in range(15)]
        result = _result(amenities=amenities)
        msg = format_analysis_message(_listing(), result, Language.EN)
        assert "Feature9" in msg
        assert "Feature10" in msg
        assert "Feature14" in msg

    def test_amenities_html_escaped(self):
        result = _result(amenities=["Pool & Spa", "<Hot tub>"])
        msg = format_analysis_message(_listing(), result, Language.EN)
        assert "Pool &amp; Spa" in msg
        assert "&lt;Hot tub&gt;" in msg
        assert "<Hot tub>" not in msg

    def test_amenities_label_localized_russian(self):
        result = _result(amenities=["WiFi"])
        msg = format_analysis_message(_listing(), result, Language.RU)
        assert "<b>Удобства:</b>" in msg

    def test_amenities_label_localized_spanish(self):
        result = _result(amenities=["WiFi"])
        msg = format_analysis_message(_listing(), result, Language.ES)
        assert "<b>Servicios:</b>" in msg

    def test_amenities_appear_before_price_section(self):
        result = _result(amenities=["WiFi", "Kitchen"])
        msg = format_analysis_message(_listing(), result, Language.EN)
        amenities_pos = msg.index("<b>Amenities:</b>")
        price_pos = msg.index("<b>Price:")
        assert amenities_pos < price_pos

    def test_long_amenities_does_not_truncate_price_verdict(self):
        """Very long amenities list must not push the price verdict out of the message."""
        # 200 long amenity strings easily exceed the 4096-char budget if uncapped
        amenities = [f"Amenity number {i} with a descriptive name" for i in range(200)]
        result = _result(
            amenities=amenities,
            price_verdict=PriceVerdict.OVERPRICED,
            price_explanation="Much higher than comparable listings.",
        )
        msg = format_analysis_message(_listing(), result, Language.EN)
        assert len(msg) <= _TELEGRAM_MAX_CHARS
        # Price verdict must always survive regardless of amenities length
        assert "<b>Price: Overpriced</b>" in msg
        assert "Much higher than comparable listings." in msg

    def test_long_amenities_adds_overflow_note(self):
        """When amenities are truncated, a [+N more] marker must appear."""
        amenities = [f"Amenity number {i} with a descriptive name" for i in range(200)]
        result = _result(amenities=amenities)
        msg = format_analysis_message(_listing(), result, Language.EN)
        assert "[+" in msg and "more]" in msg

    def test_near_limit_amenities_not_truncated_when_fits(self):
        """Full amenities list must be preserved when it fits within the exact
        -2 separator budget and would only overflow with the over-conservative
        old -4 budget.

        Layout with minimal inputs (EN, no strengths/risks, no price explanation):
          message_without = "<b>A</b>\\n\\nB\\n\\n<b>Price: Fair</b>" = 30 chars
          correct budget = 4096 - 30 - 2 = 4064
          old wrong budget = 4096 - 30 - 4 = 4062
        Amenities section for one "X"*4043 amenity:
          "<b>Amenities:</b>" (17) + "\\n" (1) + "- " (2) + "X"*4043 = 4063 chars
          4063 <= 4064 (correct) → full render, no overflow note
          4063 > 4062 (old)     → compact overflow → "[+1 more]"
        Total message = 30 + 2 + 4063 = 4095 <= 4096.
        """
        amenity_name = "X" * 4043
        result = _result(
            display_title="A",
            summary="B",
            strengths=[],
            risks=[],
            price_verdict=PriceVerdict.FAIR,
            price_explanation="",
            amenities=[amenity_name],
        )
        msg = format_analysis_message(_listing(), result, Language.EN)
        assert len(msg) <= _TELEGRAM_MAX_CHARS
        assert amenity_name in msg, "full amenity must appear — no overflow truncation"
        assert "[+" not in msg, "no overflow note should appear when amenities fit exactly"

    def test_tight_budget_shows_compact_overflow_not_empty(self):
        """When budget fits the header + overflow note but not any bullet, the
        section must still appear with a compact [+N more] marker rather than
        being silently dropped."""
        from src.i18n.types import Language as Lang

        amenities = ["WiFi", "Kitchen", "Washer"]
        fake_result = _result(amenities=amenities)
        # Budget is calibrated so the compact overflow marker fits but no real
        # bullet does.  Measured values (EN):
        #   header "<b>Amenities:</b>" = 17 chars
        #   compact_section = header + "\n" + "- [+3 more]" = 29 chars
        #   bullets_budget at budget=30 → 30 - 17 - 1 = 12
        #   first trial "- WiFi\n- [+2 more]" = 18 chars > 12 → bullet rejected
        #   compact_overflow "- [+3 more]" = 11 chars ≤ 12 → compact returned
        section = _format_amenities(fake_result, Lang.EN, budget=30)
        assert section != "", "section must not be empty when budget fits compact overflow"
        assert "[+3 more]" in section
        assert "- WiFi" not in section  # no individual bullet should appear

    def test_overflow_marker_localized_russian(self):
        """Overflow marker must use the Russian catalog string, not English."""
        amenities = [f"Amenity number {i} with a descriptive name" for i in range(200)]
        result = _result(amenities=amenities)
        msg = format_analysis_message(_listing(), result, Language.RU)
        assert len(msg) <= _TELEGRAM_MAX_CHARS
        assert "[+" in msg
        assert "ещё]" in msg
        assert "more]" not in msg

    def test_overflow_marker_localized_spanish(self):
        """Overflow marker must use the Spanish catalog string, not English."""
        amenities = [f"Amenity number {i} with a descriptive name" for i in range(200)]
        result = _result(amenities=amenities)
        msg = format_analysis_message(_listing(), result, Language.ES)
        assert len(msg) <= _TELEGRAM_MAX_CHARS
        assert "[+" in msg
        assert "más]" in msg
        assert "more]" not in msg
