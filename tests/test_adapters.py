"""Tests for provider detection and the Airbnb adapter contract.

Covers:
- AirbnbAdapter.supports_url — full matrix of positive and negative cases
- detect_provider — maps URLs to ListingProvider enum values
- resolve_adapter — returns the correct adapter instance or None

Apify-backed fetch and normalization tests live in test_airbnb_extraction.py.
"""

import pytest

from src.adapters.airbnb import AirbnbAdapter
from src.adapters.base import ListingAdapter
from src.adapters.registry import detect_provider, resolve_adapter
from src.domain.listing import ListingProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def airbnb_adapter() -> AirbnbAdapter:
    return AirbnbAdapter()


# ---------------------------------------------------------------------------
# AirbnbAdapter — class contract
# ---------------------------------------------------------------------------


class TestAirbnbAdapterContract:
    def test_is_listing_adapter_subclass(self, airbnb_adapter):
        assert isinstance(airbnb_adapter, ListingAdapter)

    def test_provider_is_airbnb(self, airbnb_adapter):
        assert airbnb_adapter.provider == ListingProvider.AIRBNB

# ---------------------------------------------------------------------------
# AirbnbAdapter.supports_url — positive cases
# ---------------------------------------------------------------------------


class TestAirbnbAdapterSupportsUrlPositive:
    def test_airbnb_com_listing(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://www.airbnb.com/rooms/123") is True

    def test_airbnb_apex_domain(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://airbnb.com/rooms/123") is True

    def test_airbnb_co_uk(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://www.airbnb.co.uk/rooms/456") is True

    def test_airbnb_co_uk_apex(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://airbnb.co.uk/rooms/456") is True

    def test_airbnb_de(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://www.airbnb.de/rooms/789") is True

    def test_airbnb_ru(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://www.airbnb.ru/rooms/789") is True

    def test_airbnb_com_au(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://www.airbnb.com.au/rooms/1") is True

    def test_airbnb_xyz_supported_without_allowlist(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://www.airbnb.xyz/rooms/1") is True

    def test_airbnb_com_listing_with_trailing_slash(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://airbnb.com/rooms/99/") is True

    def test_abnb_me_short_link(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://abnb.me/abc123") is True

    def test_abnb_me_www_subdomain(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://www.abnb.me/abc123") is True

    def test_airbnb_http_scheme_accepted(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("http://airbnb.com/rooms/123") is True


# ---------------------------------------------------------------------------
# AirbnbAdapter.supports_url — negative cases
# ---------------------------------------------------------------------------


class TestAirbnbAdapterSupportsUrlNegative:
    def test_booking_com_rejected(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://www.booking.com/hotel/1") is False

    def test_airbnb_help_page_rejected(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://www.airbnb.com/help/article/1") is False

    def test_airbnb_search_url_rejected(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://www.airbnb.com/s/Paris--France") is False

    def test_airbnb_home_page_rejected(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://www.airbnb.com/") is False

    def test_airbnb_bare_rooms_path_rejected(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://www.airbnb.com/rooms/") is False

    def test_airbnb_rooms_no_slash_rejected(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://www.airbnb.com/rooms") is False

    def test_airbnb_extra_path_segment_rejected(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://www.airbnb.com/rooms/123/photos") is False

    def test_airbnb_lookalike_subdomain_rejected(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://airbnb.evil.com/rooms/1") is False

    def test_abnb_me_root_path_rejected(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://abnb.me/") is False

    def test_abnb_me_no_path_rejected(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://abnb.me") is False

    def test_abnb_me_lookalike_rejected(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://notabnb.me/abc123") is False

    def test_ftp_scheme_rejected(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("ftp://airbnb.com/rooms/123") is False

    def test_javascript_scheme_rejected(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("javascript://airbnb.com/rooms/123") is False

    def test_file_scheme_rejected(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("file:///airbnb.com/rooms/123") is False

    def test_notairbnb_com_rejected(self, airbnb_adapter):
        assert airbnb_adapter.supports_url("https://notairbnb.com/rooms/1") is False


# ---------------------------------------------------------------------------
# detect_provider
# ---------------------------------------------------------------------------


class TestDetectProvider:
    def test_airbnb_com_returns_airbnb(self):
        assert detect_provider("https://www.airbnb.com/rooms/123") == ListingProvider.AIRBNB

    def test_airbnb_localized_domain_returns_airbnb(self):
        assert detect_provider("https://airbnb.de/rooms/1") == ListingProvider.AIRBNB

    def test_airbnb_ru_returns_airbnb(self):
        assert detect_provider("https://www.airbnb.ru/rooms/1") == ListingProvider.AIRBNB

    def test_abnb_me_returns_airbnb(self):
        assert detect_provider("https://abnb.me/xyz") == ListingProvider.AIRBNB

    def test_booking_com_returns_unknown(self):
        assert detect_provider("https://www.booking.com/hotel/1") == ListingProvider.UNKNOWN

    def test_random_url_returns_unknown(self):
        assert detect_provider("https://example.com/flat/42") == ListingProvider.UNKNOWN

    def test_non_listing_airbnb_page_returns_unknown(self):
        assert detect_provider("https://www.airbnb.com/help/article/1") == ListingProvider.UNKNOWN

    def test_empty_string_returns_unknown(self):
        assert detect_provider("") == ListingProvider.UNKNOWN


# ---------------------------------------------------------------------------
# resolve_adapter
# ---------------------------------------------------------------------------


class TestResolveAdapter:
    def test_airbnb_url_returns_airbnb_adapter(self):
        adapter = resolve_adapter("https://www.airbnb.com/rooms/123")
        assert adapter is not None
        assert isinstance(adapter, AirbnbAdapter)

    def test_abnb_me_url_returns_airbnb_adapter(self):
        adapter = resolve_adapter("https://abnb.me/abc")
        assert adapter is not None
        assert adapter.provider == ListingProvider.AIRBNB

    def test_unsupported_url_returns_none(self):
        assert resolve_adapter("https://www.booking.com/hotel/1") is None

    def test_empty_url_returns_none(self):
        assert resolve_adapter("") is None

    def test_returned_adapter_reports_correct_provider(self):
        adapter = resolve_adapter("https://airbnb.co.uk/rooms/99")
        assert adapter is not None
        assert adapter.provider == ListingProvider.AIRBNB
