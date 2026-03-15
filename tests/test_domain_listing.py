"""Tests for normalized listing domain models.

These tests verify model construction, field defaults, validation, and the
expected shape of each model — without requiring a live database.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from src.domain.listing import (
    AnalysisJob,
    JobStatus,
    ListingLocation,
    ListingProvider,
    NormalizedListing,
    PriceInfo,
)


# ---------------------------------------------------------------------------
# ListingProvider
# ---------------------------------------------------------------------------


class TestListingProvider:
    def test_airbnb_value(self):
        assert ListingProvider.AIRBNB == "airbnb"

    def test_unknown_value(self):
        assert ListingProvider.UNKNOWN == "unknown"

    def test_str_roundtrip(self):
        assert ListingProvider("airbnb") is ListingProvider.AIRBNB


# ---------------------------------------------------------------------------
# JobStatus
# ---------------------------------------------------------------------------


class TestJobStatus:
    def test_all_statuses_exist(self):
        statuses = {s.value for s in JobStatus}
        assert statuses == {"pending", "running", "completed", "failed"}

    def test_default_is_pending(self):
        job = AnalysisJob(
            source_url="https://airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1,
            telegram_message_id=1,
        )
        assert job.status is JobStatus.PENDING


# ---------------------------------------------------------------------------
# ListingLocation
# ---------------------------------------------------------------------------


class TestListingLocation:
    def test_all_optional_fields_default_to_none(self):
        loc = ListingLocation()
        assert loc.latitude is None
        assert loc.longitude is None
        assert loc.address is None
        assert loc.city is None
        assert loc.country is None
        assert loc.neighbourhood is None

    def test_construct_with_coordinates(self):
        loc = ListingLocation(latitude=48.8566, longitude=2.3522, city="Paris")
        assert loc.latitude == pytest.approx(48.8566)
        assert loc.longitude == pytest.approx(2.3522)
        assert loc.city == "Paris"


# ---------------------------------------------------------------------------
# PriceInfo
# ---------------------------------------------------------------------------


class TestPriceInfo:
    def test_required_fields(self):
        p = PriceInfo(amount=Decimal("150.00"), currency="USD")
        assert p.amount == Decimal("150.00")
        assert p.currency == "USD"
        assert p.period == "night"  # default

    def test_optional_fees_default_to_none(self):
        p = PriceInfo(amount=Decimal("200"), currency="EUR")
        assert p.cleaning_fee is None
        assert p.service_fee is None

    def test_all_fee_fields(self):
        p = PriceInfo(
            amount=Decimal("120"),
            currency="GBP",
            period="night",
            cleaning_fee=Decimal("30"),
            service_fee=Decimal("20"),
        )
        assert p.cleaning_fee == Decimal("30")
        assert p.service_fee == Decimal("20")


# ---------------------------------------------------------------------------
# NormalizedListing
# ---------------------------------------------------------------------------


class TestNormalizedListing:
    def _minimal(self, **overrides) -> NormalizedListing:
        defaults = dict(
            provider=ListingProvider.AIRBNB,
            source_url="https://www.airbnb.com/rooms/12345",
            source_id="12345",
            title="Cosy flat in the city centre",
        )
        defaults.update(overrides)
        return NormalizedListing(**defaults)

    def test_id_is_uuid_by_default(self):
        listing = self._minimal()
        assert isinstance(listing.id, uuid.UUID)

    def test_ids_are_unique_per_instance(self):
        a = self._minimal()
        b = self._minimal()
        assert a.id != b.id

    def test_custom_id_is_respected(self):
        fixed = uuid.UUID("12345678-1234-5678-1234-567812345678")
        listing = self._minimal(id=fixed)
        assert listing.id == fixed

    def test_required_fields_stored(self):
        listing = self._minimal()
        assert listing.provider is ListingProvider.AIRBNB
        assert listing.source_url == "https://www.airbnb.com/rooms/12345"
        assert listing.source_id == "12345"
        assert listing.title == "Cosy flat in the city centre"

    def test_optional_fields_default_to_none_or_empty(self):
        listing = self._minimal()
        assert listing.description is None
        assert listing.price is None
        assert listing.bedrooms is None
        assert listing.bathrooms is None
        assert listing.max_guests is None
        assert listing.amenities == []
        assert listing.rating is None
        assert listing.review_count is None
        assert listing.host_name is None
        assert listing.host_is_superhost is None

    def test_location_defaults_to_empty_location(self):
        listing = self._minimal()
        assert isinstance(listing.location, ListingLocation)
        assert listing.location.latitude is None

    def test_created_at_and_updated_at_set(self):
        listing = self._minimal()
        assert listing.created_at is not None
        assert listing.updated_at is not None

    def test_full_listing(self):
        listing = NormalizedListing(
            provider=ListingProvider.AIRBNB,
            source_url="https://www.airbnb.com/rooms/99",
            source_id="99",
            title="Penthouse",
            description="Stunning views",
            location=ListingLocation(latitude=51.5, longitude=-0.1, city="London"),
            price=PriceInfo(amount=Decimal("300"), currency="GBP"),
            bedrooms=3,
            bathrooms=2.0,
            max_guests=6,
            amenities=["WiFi", "Pool"],
            rating=4.9,
            review_count=120,
            host_name="Jane",
            host_is_superhost=True,
        )
        assert listing.location.city == "London"
        assert listing.amenities == ["WiFi", "Pool"]
        assert listing.host_is_superhost is True

    def test_no_raw_payload_field(self):
        """NormalizedListing must remain provider-agnostic; raw_payload lives in persistence only."""
        listing = self._minimal()
        assert not hasattr(listing, "raw_payload")


# ---------------------------------------------------------------------------
# AnalysisJob
# ---------------------------------------------------------------------------


class TestAnalysisJob:
    def _make(self, **overrides) -> AnalysisJob:
        defaults = dict(
            source_url="https://www.airbnb.com/rooms/12345",
            provider=ListingProvider.AIRBNB,
            telegram_chat_id=1001,
            telegram_message_id=42,
        )
        defaults.update(overrides)
        return AnalysisJob(**defaults)

    def test_id_is_uuid_by_default(self):
        job = self._make()
        assert isinstance(job.id, uuid.UUID)

    def test_ids_are_unique_per_instance(self):
        assert self._make().id != self._make().id

    def test_default_status_is_pending(self):
        assert self._make().status is JobStatus.PENDING

    def test_listing_id_starts_as_none(self):
        assert self._make().listing_id is None

    def test_error_message_starts_as_none(self):
        assert self._make().error_message is None

    def test_status_transitions(self):
        job = self._make()
        job.status = JobStatus.RUNNING
        assert job.status is JobStatus.RUNNING
        job.status = JobStatus.COMPLETED
        assert job.status is JobStatus.COMPLETED

    def test_link_listing_id(self):
        listing_uuid = uuid.uuid4()
        job = self._make(listing_id=listing_uuid)
        assert job.listing_id == listing_uuid

    def test_telegram_fields_stored(self):
        job = self._make(telegram_chat_id=5001, telegram_message_id=77)
        assert job.telegram_chat_id == 5001
        assert job.telegram_message_id == 77

    def test_large_negative_chat_id(self):
        """Supergroup/channel chat IDs are 64-bit signed values; ensure no overflow."""
        large_id = -1001234567890
        job = self._make(telegram_chat_id=large_id)
        assert job.telegram_chat_id == large_id
