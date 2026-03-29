"""Tests for the simple amenities block (spec 031).

Covers:
- AnalysisResult carries amenities field
- Telegram formatter renders amenities as a dedicated section
- Amenities section omitted when list is empty
- Long amenity lists are capped at 10 items
- Amenity strings are HTML-escaped
- i18n labels work for all supported languages
- Translation service passes amenities through (and falls back gracefully)
"""

from __future__ import annotations

import json

import pytest

from src.analysis.result import AnalysisResult, PriceVerdict
from src.domain.listing import ListingProvider, NormalizedListing
from src.i18n.types import Language
from src.telegram.formatter import format_analysis_message
from src.translation.service import _build_translation_prompt, _parse_translation_response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _listing(**overrides) -> NormalizedListing:
    base = {
        "provider": ListingProvider.AIRBNB,
        "source_url": "https://www.airbnb.com/rooms/99",
        "source_id": "99",
        "title": "Test Apartment",
    }
    base.update(overrides)
    return NormalizedListing(**base)


def _result(**overrides) -> AnalysisResult:
    base = {
        "summary": "Nice place.",
        "price_verdict": PriceVerdict.FAIR,
    }
    base.update(overrides)
    return AnalysisResult(**base)


# ---------------------------------------------------------------------------
# AnalysisResult model
# ---------------------------------------------------------------------------


class TestAnalysisResultAmenities:
    def test_amenities_defaults_to_empty_list(self):
        r = _result()
        assert r.amenities == []

    def test_amenities_stores_given_list(self):
        r = _result(amenities=["WiFi", "Kitchen", "Pool"])
        assert r.amenities == ["WiFi", "Kitchen", "Pool"]

    def test_model_copy_preserves_amenities(self):
        r = _result(amenities=["WiFi"])
        r2 = r.model_copy(update={"summary": "Updated."})
        assert r2.amenities == ["WiFi"]


# ---------------------------------------------------------------------------
# Telegram formatter
# ---------------------------------------------------------------------------


class TestAmenitiesFormatterSection:
    def test_amenities_section_present_when_non_empty(self):
        msg = format_analysis_message(
            _listing(),
            _result(amenities=["WiFi", "Kitchen"]),
            Language.EN,
        )
        assert "<b>Amenities:</b>" in msg
        assert "WiFi" in msg
        assert "Kitchen" in msg

    def test_amenities_section_omitted_when_empty(self):
        msg = format_analysis_message(_listing(), _result(amenities=[]), Language.EN)
        assert "Amenities:" not in msg

    def test_amenities_capped_at_ten_items(self):
        many = [f"Item{i}" for i in range(20)]
        msg = format_analysis_message(_listing(), _result(amenities=many), Language.EN)
        # Items 0-9 should appear, 10-19 should not
        assert "Item9" in msg
        assert "Item10" not in msg

    def test_amenities_html_escaped(self):
        msg = format_analysis_message(
            _listing(),
            _result(amenities=["Wi-Fi & TV", "<Pool>"]),
            Language.EN,
        )
        assert "Wi-Fi &amp; TV" in msg
        assert "&lt;Pool&gt;" in msg

    def test_amenities_section_appears_after_risks(self):
        msg = format_analysis_message(
            _listing(),
            _result(
                risks=["Noisy street"],
                amenities=["WiFi", "Kitchen"],
            ),
            Language.EN,
        )
        risks_pos = msg.index("Noisy street")
        amenities_pos = msg.index("Amenities:")
        assert amenities_pos > risks_pos

    def test_russian_amenities_label(self):
        msg = format_analysis_message(
            _listing(),
            _result(amenities=["WiFi"]),
            Language.RU,
        )
        assert "<b>Удобства:</b>" in msg

    def test_spanish_amenities_label(self):
        msg = format_analysis_message(
            _listing(),
            _result(amenities=["WiFi"]),
            Language.ES,
        )
        assert "<b>Servicios:</b>" in msg

    def test_amenities_comma_separated(self):
        msg = format_analysis_message(
            _listing(),
            _result(amenities=["WiFi", "Kitchen", "Pool"]),
            Language.EN,
        )
        assert "WiFi, Kitchen, Pool" in msg


# ---------------------------------------------------------------------------
# Translation stage
# ---------------------------------------------------------------------------


class TestAmenitiesTranslation:
    def test_amenities_included_in_translation_prompt(self):
        r = _result(amenities=["WiFi", "Kitchen"])
        prompt = _build_translation_prompt(r, Language.RU)
        assert "amenities" in prompt
        assert "WiFi" in prompt

    def test_parse_response_carries_translated_amenities(self):
        original = _result(amenities=["WiFi", "Kitchen"])
        translated_response = json.dumps(
            {
                "display_title": "Test",
                "summary": "Хорошее место.",
                "strengths": [],
                "risks": [],
                "price_explanation": "",
                "amenities": ["Вайфай", "Кухня"],
                "review_overall_assessment": "",
                "review_critical_red_flags": [],
                "review_recurring_issues": [],
                "review_conflicts_or_disputes": [],
                "review_positive_signals": [],
                "review_window_view_summary": "",
            }
        )
        result = _parse_translation_response(translated_response, original)
        assert result.amenities == ["Вайфай", "Кухня"]

    def test_parse_response_falls_back_to_original_amenities_on_malformed(self):
        original = _result(amenities=["WiFi", "Kitchen"])
        # amenities field is wrong type
        bad_response = json.dumps(
            {
                "display_title": "Test",
                "summary": "Хорошее место.",
                "strengths": [],
                "risks": [],
                "price_explanation": "",
                "amenities": "not-a-list",
                "review_overall_assessment": "",
                "review_critical_red_flags": [],
                "review_recurring_issues": [],
                "review_conflicts_or_disputes": [],
                "review_positive_signals": [],
                "review_window_view_summary": "",
            }
        )
        result = _parse_translation_response(bad_response, original)
        assert result.amenities == ["WiFi", "Kitchen"]

    def test_parse_response_empty_amenities_stays_empty(self):
        original = _result(amenities=[])
        response = json.dumps(
            {
                "display_title": "Test",
                "summary": "Хорошее место.",
                "strengths": [],
                "risks": [],
                "price_explanation": "",
                "amenities": [],
                "review_overall_assessment": "",
                "review_critical_red_flags": [],
                "review_recurring_issues": [],
                "review_conflicts_or_disputes": [],
                "review_positive_signals": [],
                "review_window_view_summary": "",
            }
        )
        result = _parse_translation_response(response, original)
        assert result.amenities == []
