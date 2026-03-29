"""Focused tests for amenities insights mapping, translation preservation, and formatter rendering."""

from __future__ import annotations

import json

from src.analysis.modules.amenities import AmenitiesEvidenceResult
from src.analysis.result import (
    AmenitiesInsightsBlock,
    AnalysisResult,
    PriceVerdict,
)
from src.domain.amenity_corpus import AmenityCorpus
from src.domain.listing import ListingProvider, NormalizedListing
from src.i18n.types import Language
from src.jobs.processor import _map_amenities_result
from src.telegram.formatter import _format_amenities_insights, format_analysis_message
from src.translation.service import _parse_translation_response


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


class TestProcessorMapping:
    def test_maps_keys_and_grouped_sections_into_amenities_block(self):
        result = AmenitiesEvidenceResult(
            module_name="amenities_evidence",
            corpus=AmenityCorpus(
                source_provider="airbnb",
                items=[
                    # Home comfort
                    __import__("src.domain.amenity_corpus", fromlist=["UnifiedAmenityItem", "AmenityAvailability"]).UnifiedAmenityItem(
                        source_provider="airbnb",
                        canonical_key="bathtub",
                        label="Bathtub",
                        category="bathroom",
                        availability=__import__("src.domain.amenity_corpus", fromlist=["AmenityAvailability"]).AmenityAvailability.AVAILABLE,
                    ),
                    __import__("src.domain.amenity_corpus", fromlist=["UnifiedAmenityItem", "AmenityAvailability"]).UnifiedAmenityItem(
                        source_provider="airbnb",
                        canonical_key="washer",
                        label="Free washer – In building",
                        category="laundry",
                        availability=__import__("src.domain.amenity_corpus", fromlist=["AmenityAvailability"]).AmenityAvailability.AVAILABLE,
                    ),
                    # Kitchen
                    __import__("src.domain.amenity_corpus", fromlist=["UnifiedAmenityItem", "AmenityAvailability"]).UnifiedAmenityItem(
                        source_provider="airbnb",
                        canonical_key="kitchen",
                        label="Kitchen",
                        category="kitchen",
                        availability=__import__("src.domain.amenity_corpus", fromlist=["AmenityAvailability"]).AmenityAvailability.AVAILABLE,
                    ),
                    __import__("src.domain.amenity_corpus", fromlist=["UnifiedAmenityItem", "AmenityAvailability"]).UnifiedAmenityItem(
                        source_provider="airbnb",
                        canonical_key="microwave",
                        label="Microwave",
                        category="kitchen",
                        availability=__import__("src.domain.amenity_corpus", fromlist=["AmenityAvailability"]).AmenityAvailability.AVAILABLE,
                    ),
                    # Outdoor/facilities
                    __import__("src.domain.amenity_corpus", fromlist=["UnifiedAmenityItem", "AmenityAvailability"]).UnifiedAmenityItem(
                        source_provider="airbnb",
                        canonical_key="pool",
                        label="Pool",
                        category="leisure",
                        availability=__import__("src.domain.amenity_corpus", fromlist=["AmenityAvailability"]).AmenityAvailability.AVAILABLE,
                    ),
                ],
            ),
            available_keys=["wifi", "kitchen", "pool"],
            critical_missing_keys=["smoke_alarm", "heating"],
        )
        block = _map_amenities_result(result)
        assert block is not None
        assert block.available_keys == ["wifi", "kitchen", "pool"]
        assert block.critical_missing_keys == ["smoke_alarm", "heating"]
        assert [section.section_id for section in block.sections] == [
            "home_comfort",
            "kitchen_dining",
            "outdoor_facilities",
        ]
        assert block.sections[1].amenity_keys == ["kitchen", "microwave"]

    def test_returns_none_for_empty_result(self):
        result = AmenitiesEvidenceResult(
            module_name="amenities_evidence",
            corpus=AmenityCorpus(source_provider="airbnb"),
        )
        assert _map_amenities_result(result) is None


class TestTranslationPreservation:
    def test_translation_parser_preserves_amenities_block(self):
        original = _base_result(
            amenities_insights=AmenitiesInsightsBlock(
                available_keys=["wifi", "kitchen", "pool"],
                critical_missing_keys=["smoke_alarm"],
                sections=[
                    AmenitiesInsightsBlock.Section(
                        section_id="kitchen_dining",
                        amenity_keys=["kitchen", "microwave"],
                    )
                ],
            )
        )
        raw = json.dumps(
            {
                "display_title": "Apartamento",
                "summary": "Buen lugar.",
                "strengths": ["Buena ubicación"],
                "risks": ["Algo de ruido"],
                "price_explanation": "Precio justo.",
            }
        )
        translated = _parse_translation_response(raw, original)
        assert translated.amenities_insights is not None
        assert translated.amenities_insights.available_keys == ["wifi", "kitchen", "pool"]
        assert translated.amenities_insights.critical_missing_keys == ["smoke_alarm"]
        assert translated.amenities_insights.sections[0].section_id == "kitchen_dining"
        assert translated.amenities_insights.sections[0].amenity_keys == ["kitchen", "microwave"]


class TestFormatterAmenitiesBlock:
    def test_formatter_renders_key_amenities_and_missing(self):
        result = _base_result(
            amenities_insights=AmenitiesInsightsBlock(
                available_keys=["pool", "wifi", "kitchen", "washer", "parking", "air_conditioning"],
                critical_missing_keys=["smoke_alarm", "carbon_monoxide_alarm", "heating"],
                sections=[
                    AmenitiesInsightsBlock.Section(
                        section_id="home_comfort",
                        amenity_keys=["bathtub", "washer", "tv"],
                    ),
                    AmenitiesInsightsBlock.Section(
                        section_id="kitchen_dining",
                        amenity_keys=["kitchen", "refrigerator", "microwave", "kettle", "toaster"],
                    ),
                    AmenitiesInsightsBlock.Section(
                        section_id="outdoor_facilities",
                        amenity_keys=["balcony", "outdoor_dining", "bbq_grill", "parking", "pool"],
                    ),
                ],
            )
        )
        block = _format_amenities_insights(result, Language.EN)
        assert "<b>Amenities:</b>" in block
        assert "<b>Key amenities:</b> Wi-Fi, Kitchen, Air conditioning, Washer, Parking, Pool" in block
        assert "<b>Home comfort:</b> Bathtub, Washer, TV" in block
        assert "<b>Kitchen and dining:</b> Kitchen, Refrigerator, Microwave, Kettle, Toaster" in block
        assert "<b>Outdoor and facilities:</b> Balcony or patio, Outdoor dining area, BBQ grill, Parking, Pool" in block
        assert "<b>Missing or not included:</b>" in block
        assert "- Smoke alarm" in block
        assert "- Carbon monoxide alarm" in block
        assert "- Heating" in block

    def test_formatter_omits_block_when_no_insights(self):
        result = _base_result(amenities_insights=None)
        assert _format_amenities_insights(result, Language.EN) == ""

    def test_full_message_includes_amenities_block(self):
        result = _base_result(
            amenities_insights=AmenitiesInsightsBlock(
                available_keys=["wifi", "kitchen"],
                critical_missing_keys=["smoke_alarm"],
                sections=[
                    AmenitiesInsightsBlock.Section(
                        section_id="kitchen_dining",
                        amenity_keys=["kitchen", "microwave"],
                    )
                ],
            )
        )
        msg = format_analysis_message(_listing(), result, Language.EN)
        assert "<b>Amenities:</b>" in msg
        assert "<b>Key amenities:</b> Wi-Fi, Kitchen" in msg
        assert "<b>Kitchen and dining:</b> Kitchen, Microwave" in msg
        assert "- Smoke alarm" in msg
