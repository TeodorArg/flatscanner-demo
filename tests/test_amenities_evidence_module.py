"""Tests for the amenities evidence module and normalizers."""

from __future__ import annotations

import pytest

from src.analysis.amenities.normalizers.airbnb import AirbnbAmenityNormalizer
from src.analysis.amenities.normalizers.generic import GenericAmenityNormalizer
from src.analysis.context import AnalysisContext
from src.analysis.modules.amenities import (
    AirbnbAmenitiesEvidenceModule,
    AmenitiesEvidenceResult,
    GenericAmenitiesEvidenceModule,
)
from src.domain.listing import ListingProvider, NormalizedListing
from src.domain.raw_payload import RawPayload


def _listing(
    provider: ListingProvider = ListingProvider.AIRBNB,
    *,
    amenities: list[str] | None = None,
) -> NormalizedListing:
    return NormalizedListing(
        provider=provider,
        source_url="https://www.airbnb.com/rooms/1434837151247448041",
        source_id="1434837151247448041",
        title="Palermo Hollywood Apartment",
        amenities=amenities or [],
    )


def _airbnb_payload() -> dict:
    return {
        "title": "Palermo Hollywood Apartment",
        "amenities": [
            {
                "title": "Internet and office",
                "values": [
                    {
                        "title": "Wifi",
                        "subtitle": "",
                        "available": True,
                    }
                ],
            },
            {
                "title": "Kitchen and dining",
                "values": [
                    {
                        "title": "Kitchen",
                        "subtitle": "Space where guests can cook their own meals",
                        "available": True,
                    },
                    {
                        "title": "Microwave",
                        "subtitle": "",
                        "available": True,
                    },
                ],
            },
            {
                "title": "Parking and facilities",
                "values": [
                    {
                        "title": "Free street parking",
                        "subtitle": "",
                        "available": True,
                    },
                    {
                        "title": "Pool",
                        "subtitle": "",
                        "available": True,
                    },
                ],
            },
            {
                "title": "Not included",
                "values": [
                    {
                        "title": "Smoke alarm",
                        "subtitle": "This place may not have a smoke detector.",
                        "available": False,
                    },
                    {
                        "title": "Carbon monoxide alarm",
                        "subtitle": "This place may not have a carbon monoxide detector.",
                        "available": False,
                    },
                    {
                        "title": "Heating",
                        "subtitle": "",
                        "available": False,
                    },
                ],
            },
        ],
    }


class TestAirbnbAmenityNormalizer:
    def test_flattens_nested_airbnb_amenities(self):
        listing = _listing()
        normalizer = AirbnbAmenityNormalizer()

        extraction = normalizer.normalize(_airbnb_payload(), listing)

        labels = [item.label for item in extraction.corpus.items]
        assert "Wifi" in labels
        assert "Kitchen" in labels
        assert "Free street parking" in labels
        assert "Smoke alarm" in labels
        assert "Internet and office" not in labels
        assert "Kitchen and dining" not in labels

    def test_preserves_availability_and_groups(self):
        listing = _listing()
        normalizer = AirbnbAmenityNormalizer()

        extraction = normalizer.normalize(_airbnb_payload(), listing)
        items = {item.label: item for item in extraction.corpus.items}

        assert items["Wifi"].availability.value == "available"
        assert items["Wifi"].source_group == "Internet and office"
        assert items["Smoke alarm"].availability.value == "unavailable"
        assert items["Smoke alarm"].source_group == "Not included"
        assert items["Kitchen"].category == "kitchen"
        assert items["Free street parking"].canonical_key == "parking"


class TestGenericAmenityNormalizer:
    def test_builds_items_from_listing_amenities(self):
        listing = _listing(ListingProvider.UNKNOWN, amenities=["Wifi", "Kitchen", "Pool"])
        normalizer = GenericAmenityNormalizer()

        extraction = normalizer.normalize({}, listing)

        assert [item.label for item in extraction.corpus.items] == ["Wifi", "Kitchen", "Pool"]
        assert all(item.availability.value == "available" for item in extraction.corpus.items)


class TestAmenitiesEvidenceModule:
    @pytest.mark.asyncio
    async def test_airbnb_module_returns_structured_result(self):
        listing = _listing()
        payload = RawPayload(
            provider="airbnb",
            source_url=listing.source_url,
            source_id=listing.source_id,
            payload=_airbnb_payload(),
        )
        ctx = AnalysisContext(listing=listing, raw_payload=payload)
        mod = AirbnbAmenitiesEvidenceModule()

        result = await mod.run(ctx)

        assert isinstance(result, AmenitiesEvidenceResult)
        assert result.module_name == "amenities_evidence"
        assert "wifi" in result.available_keys
        assert "kitchen" in result.available_keys
        assert "pool" in result.available_keys
        assert "smoke_alarm" in result.unavailable_keys
        assert "smoke_alarm" in result.critical_missing_keys
        assert "carbon_monoxide_alarm" in result.critical_missing_keys
        assert "heating" in result.critical_missing_keys
        assert "internet" in result.categories_present
        assert "kitchen" in result.categories_present
        assert "parking" in result.categories_present

    @pytest.mark.asyncio
    async def test_generic_module_falls_back_to_listing_amenities(self):
        listing = _listing(ListingProvider.UNKNOWN, amenities=["Wifi", "Kitchen"])
        ctx = AnalysisContext(listing=listing)
        mod = GenericAmenitiesEvidenceModule()

        result = await mod.run(ctx)

        assert result.available_keys == ["kitchen", "wifi"]
        assert result.unavailable_keys == []
        assert result.critical_missing_keys == []
