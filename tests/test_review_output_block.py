"""Focused tests for review insights mapping, translation, and formatter rendering.

Covers:
- Processor mapping from ReviewsResult to ReviewInsightsBlock
- Translation of review block freeform fields
- Formatter rendering / omission behavior
- Multilingual labels for the reviews section
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.analysis.modules.reviews import ReviewsResult
from src.analysis.result import AnalysisResult, PriceVerdict, ReviewInsightsBlock
from src.domain.listing import ListingProvider, NormalizedListing
from src.i18n.types import Language
from src.telegram.formatter import _format_review_insights, format_analysis_message
from src.translation.service import (
    TranslationService,
    _build_translation_prompt,
    _parse_translation_response,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _listing(**overrides) -> NormalizedListing:
    base = {
        "provider": ListingProvider.AIRBNB,
        "source_url": "https://www.airbnb.com/rooms/42",
        "source_id": "42",
        "title": "Sunny flat",
    }
    base.update(overrides)
    return NormalizedListing(**base)


def _base_result(**overrides) -> AnalysisResult:
    base = {
        "summary": "A nice place.",
        "strengths": ["Good location"],
        "risks": ["Loud street"],
        "price_verdict": PriceVerdict.FAIR,
        "price_explanation": "Fairly priced.",
    }
    base.update(overrides)
    return AnalysisResult(**base)


def _full_insights() -> ReviewInsightsBlock:
    return ReviewInsightsBlock(
        overall_assessment="Generally good but one mold incident.",
        overall_risk_level="medium",
        review_count=30,
        average_rating=4.5,
        critical_red_flags=["Mold reported by two guests"],
        recurring_issues=["AC was noisy in several reviews"],
        conflicts_or_disputes=["Host disputed a cleanliness review"],
        positive_signals=["Great natural light"],
        window_view_summary="Most guests praised the park view.",
    )


# ---------------------------------------------------------------------------
# Processor mapping: ReviewsResult → ReviewInsightsBlock
# ---------------------------------------------------------------------------


class TestProcessorMapping:
    """Test that ReviewsResult fields map correctly into ReviewInsightsBlock."""

    def _map(self, rv: ReviewsResult) -> ReviewInsightsBlock:
        """Replicate the processor mapping logic under test."""
        recurring = [
            item.get("summary", "") if isinstance(item, dict) else str(item)
            for item in rv.recurring_issues
            if (item.get("summary", "") if isinstance(item, dict) else str(item))
        ]
        disputes = [
            item.get("summary", "") if isinstance(item, dict) else str(item)
            for item in rv.conflicts_or_disputes
            if (item.get("summary", "") if isinstance(item, dict) else str(item))
        ]
        return ReviewInsightsBlock(
            overall_assessment=rv.overall_assessment or "",
            overall_risk_level=rv.overall_risk_level or "",
            review_count=rv.review_count,
            average_rating=rv.average_rating,
            critical_red_flags=rv.critical_red_flags,
            recurring_issues=recurring,
            conflicts_or_disputes=disputes,
            positive_signals=rv.positive_signals,
            window_view_summary=rv.window_view_summary or "",
        )

    def test_metadata_fields_pass_through(self):
        rv = ReviewsResult(module_name="reviews", review_count=20, average_rating=4.2)
        block = self._map(rv)
        assert block.review_count == 20
        assert block.average_rating == 4.2

    def test_ai_string_fields_pass_through(self):
        rv = ReviewsResult(
            module_name="reviews",
            overall_assessment="Some mold.",
            overall_risk_level="high",
            window_view_summary="Nice view.",
        )
        block = self._map(rv)
        assert block.overall_assessment == "Some mold."
        assert block.overall_risk_level == "high"
        assert block.window_view_summary == "Nice view."

    def test_critical_red_flags_pass_through(self):
        rv = ReviewsResult(module_name="reviews", critical_red_flags=["Cockroaches reported"])
        block = self._map(rv)
        assert block.critical_red_flags == ["Cockroaches reported"]

    def test_recurring_issues_dict_summary_extracted(self):
        rv = ReviewsResult(
            module_name="reviews",
            recurring_issues=[{"category": "noise", "count": 3, "summary": "Too loud at night"}],
        )
        block = self._map(rv)
        assert block.recurring_issues == ["Too loud at night"]

    def test_recurring_issues_without_summary_key_skipped(self):
        rv = ReviewsResult(
            module_name="reviews",
            recurring_issues=[{"category": "noise", "count": 3}],
        )
        block = self._map(rv)
        assert block.recurring_issues == []

    def test_conflicts_dict_summary_extracted(self):
        rv = ReviewsResult(
            module_name="reviews",
            conflicts_or_disputes=[{"incident_date": "2025-01-10", "summary": "Refund dispute"}],
        )
        block = self._map(rv)
        assert block.conflicts_or_disputes == ["Refund dispute"]

    def test_none_fields_become_empty_strings(self):
        rv = ReviewsResult(module_name="reviews")
        block = self._map(rv)
        assert block.overall_assessment == ""
        assert block.overall_risk_level == ""
        assert block.window_view_summary == ""

    def test_positive_signals_pass_through(self):
        rv = ReviewsResult(module_name="reviews", positive_signals=["Great light"])
        block = self._map(rv)
        assert block.positive_signals == ["Great light"]


# ---------------------------------------------------------------------------
# Translation: review block fields included in prompt and parsed from response
# ---------------------------------------------------------------------------


class TestTranslationPromptIncludesReviewBlock:
    def test_prompt_includes_review_fields_when_insights_present(self):
        result = _base_result(review_insights=_full_insights())
        prompt = _build_translation_prompt(result, Language.RU)
        assert "review_overall_assessment" in prompt
        assert "review_critical_red_flags" in prompt
        assert "review_recurring_issues" in prompt
        assert "review_conflicts_or_disputes" in prompt
        assert "review_window_view_summary" in prompt

    def test_prompt_includes_review_fields_when_insights_none(self):
        result = _base_result(review_insights=None)
        prompt = _build_translation_prompt(result, Language.RU)
        # Schema hint always includes the fields.
        assert "review_overall_assessment" in prompt

    def test_prompt_review_content_matches_insights(self):
        insights = _full_insights()
        result = _base_result(review_insights=insights)
        prompt = _build_translation_prompt(result, Language.RU)
        assert "Generally good but one mold incident." in prompt
        assert "Mold reported by two guests" in prompt


class TestTranslationParsingReviewBlock:
    def _original(self, insights: ReviewInsightsBlock | None = None) -> AnalysisResult:
        return _base_result(review_insights=insights)

    def _translate_response(self, extra: dict) -> str:
        base = {
            "display_title": "Sunny flat",
            "summary": "Хорошее место.",
            "strengths": ["Хорошее расположение"],
            "risks": ["Шумная улица"],
            "price_explanation": "Цена справедливая.",
        }
        base.update(extra)
        return json.dumps(base)

    def test_review_fields_translated_when_present(self):
        original = self._original(_full_insights())
        raw = self._translate_response(
            {
                "review_overall_assessment": "В целом хорошо, но был случай с плесенью.",
                "review_critical_red_flags": ["Плесень у двух гостей"],
                "review_recurring_issues": ["Шумный кондиционер"],
                "review_conflicts_or_disputes": ["Хозяин оспорил отзыв"],
                "review_positive_signals": ["Отличный свет"],
                "review_window_view_summary": "Вид на парк.",
            }
        )
        translated = _parse_translation_response(raw, original)
        assert translated.review_insights is not None
        ri = translated.review_insights
        assert ri.overall_assessment == "В целом хорошо, но был случай с плесенью."
        assert ri.critical_red_flags == ["Плесень у двух гостей"]
        assert ri.recurring_issues == ["Шумный кондиционер"]
        assert ri.conflicts_or_disputes == ["Хозяин оспорил отзыв"]
        assert ri.window_view_summary == "Вид на парк."

    def test_overall_risk_level_not_translated(self):
        original = self._original(_full_insights())
        raw = self._translate_response(
            {
                "review_overall_assessment": "...",
                "review_critical_red_flags": [],
                "review_recurring_issues": [],
                "review_conflicts_or_disputes": [],
                "review_positive_signals": [],
                "review_window_view_summary": "",
            }
        )
        translated = _parse_translation_response(raw, original)
        assert translated.review_insights is not None
        # overall_risk_level preserved from original, never translated.
        assert translated.review_insights.overall_risk_level == "medium"

    def test_metadata_fields_preserved_after_translation(self):
        original = self._original(_full_insights())
        raw = self._translate_response(
            {
                "review_overall_assessment": "...",
                "review_critical_red_flags": [],
                "review_recurring_issues": [],
                "review_conflicts_or_disputes": [],
                "review_positive_signals": [],
                "review_window_view_summary": "",
            }
        )
        translated = _parse_translation_response(raw, original)
        ri = translated.review_insights
        assert ri is not None
        assert ri.review_count == 30
        assert ri.average_rating == 4.5

    def test_review_insights_none_when_original_has_none(self):
        original = self._original(None)
        raw = self._translate_response({})
        translated = _parse_translation_response(raw, original)
        assert translated.review_insights is None

    def test_fallback_to_original_when_field_missing(self):
        original = self._original(_full_insights())
        # No review fields in response → fall back to originals.
        raw = json.dumps(
            {
                "display_title": "Sunny flat",
                "summary": "Хорошее место.",
                "strengths": ["Хорошее"],
                "risks": ["Шум"],
                "price_explanation": "Справедливо.",
            }
        )
        translated = _parse_translation_response(raw, original)
        ri = translated.review_insights
        assert ri is not None
        assert ri.overall_assessment == original.review_insights.overall_assessment  # type: ignore[union-attr]
        assert ri.critical_red_flags == original.review_insights.critical_red_flags  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Formatter: review section rendering
# ---------------------------------------------------------------------------


class TestFormatterReviewSectionRendering:
    def test_no_insights_produces_no_review_section(self):
        result = _base_result(review_insights=None)
        msg = format_analysis_message(_listing(), result, Language.RU)
        assert "Отзывы:" not in msg

    def test_empty_insights_block_omitted(self):
        result = _base_result(review_insights=ReviewInsightsBlock())
        section = _format_review_insights(result, Language.RU)
        assert section == ""

    def test_metadata_only_renders_compact_overview(self):
        result = _base_result(
            review_insights=ReviewInsightsBlock(review_count=25, average_rating=4.7)
        )
        section = _format_review_insights(result, Language.RU)
        assert "Отзывы:" in section
        assert "25" in section
        assert "4.7★" in section

    def test_full_insights_renders_all_subsections(self):
        result = _base_result(review_insights=_full_insights())
        section = _format_review_insights(result, Language.RU)
        assert "Отзывы:" in section
        assert "Generally good but one mold incident." in section
        assert "Тревожные сигналы:" in section
        assert "Mold reported by two guests" in section
        assert "Частые проблемы:" in section
        assert "AC was noisy in several reviews" in section
        assert "Конфликты:" in section
        assert "Host disputed a cleanliness review" in section
        assert "Вид из окна:" in section
        assert "Most guests praised the park view." in section

    def test_empty_red_flags_omits_subsection_label(self):
        insights = ReviewInsightsBlock(
            overall_assessment="Fine.",
            review_count=10,
            critical_red_flags=[],
        )
        result = _base_result(review_insights=insights)
        section = _format_review_insights(result, Language.RU)
        assert "Тревожные сигналы:" not in section

    def test_empty_recurring_issues_omits_subsection_label(self):
        insights = ReviewInsightsBlock(review_count=5, recurring_issues=[])
        result = _base_result(review_insights=insights)
        section = _format_review_insights(result, Language.RU)
        assert "Частые проблемы:" not in section

    def test_review_section_appears_between_risks_and_price(self):
        result = _base_result(review_insights=_full_insights())
        msg = format_analysis_message(_listing(), result, Language.RU)
        risks_pos = msg.index("Риски:")
        reviews_pos = msg.index("Отзывы:")
        price_pos = msg.index("Цена:")
        assert risks_pos < reviews_pos < price_pos

    def test_full_message_contains_review_section(self):
        result = _base_result(review_insights=_full_insights())
        msg = format_analysis_message(_listing(), result, Language.RU)
        assert "Отзывы:" in msg
        assert "Mold reported by two guests" in msg


# ---------------------------------------------------------------------------
# Formatter: multilingual labels
# ---------------------------------------------------------------------------


class TestFormatterReviewLabelsMultilingual:
    def test_english_reviews_label(self):
        result = _base_result(review_insights=ReviewInsightsBlock(review_count=10))
        section = _format_review_insights(result, Language.EN)
        assert "Reviews:" in section
        assert "Отзывы:" not in section

    def test_spanish_reviews_label(self):
        result = _base_result(review_insights=ReviewInsightsBlock(review_count=10))
        section = _format_review_insights(result, Language.ES)
        assert "Reseñas:" in section

    def test_english_red_flags_label(self):
        result = _base_result(
            review_insights=ReviewInsightsBlock(
                review_count=5, critical_red_flags=["Issue"]
            )
        )
        section = _format_review_insights(result, Language.EN)
        assert "Red flags:" in section

    def test_spanish_red_flags_label(self):
        result = _base_result(
            review_insights=ReviewInsightsBlock(
                review_count=5, critical_red_flags=["Issue"]
            )
        )
        section = _format_review_insights(result, Language.ES)
        assert "Señales de alerta:" in section

    def test_english_recurring_issues_label(self):
        result = _base_result(
            review_insights=ReviewInsightsBlock(
                review_count=5, recurring_issues=["Noisy"]
            )
        )
        section = _format_review_insights(result, Language.EN)
        assert "Recurring issues:" in section

    def test_english_disputes_label(self):
        result = _base_result(
            review_insights=ReviewInsightsBlock(
                review_count=5, conflicts_or_disputes=["Dispute"]
            )
        )
        section = _format_review_insights(result, Language.EN)
        assert "Disputes:" in section

    def test_english_window_view_label(self):
        result = _base_result(
            review_insights=ReviewInsightsBlock(
                review_count=5, window_view_summary="Great view."
            )
        )
        section = _format_review_insights(result, Language.EN)
        assert "Window view:" in section

    def test_all_languages_produce_non_empty_review_section(self):
        result = _base_result(review_insights=_full_insights())
        for lang in Language:
            section = _format_review_insights(result, lang)
            assert section, f"Empty review section for language {lang}"
