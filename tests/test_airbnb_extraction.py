"""Tests for Apify-backed Airbnb extraction and normalization.

Covers:
- ApifyClient.run_and_get_items — success, non-200 error, non-list body
- AirbnbAdapter.fetch — successful fetch + normalization, empty dataset, Apify error
- _normalize — field mapping for typical and sparse Airbnb payloads
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.adapters.airbnb import AirbnbAdapter, _build_actor_input, _normalize
from src.adapters.apify_client import ApifyClient, ApifyError
from src.adapters.base import AdapterResult
from src.app.config import Settings
from src.domain.listing import ListingProvider, NormalizedListing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_settings(**overrides: Any) -> Settings:
    """Return a testing Settings instance with safe defaults."""
    defaults: dict[str, Any] = {
        "app_env": "testing",
        "apify_api_token": "test-token",
        "apify_airbnb_actor_id": "test~actor",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _full_airbnb_payload(listing_id: str = "12345") -> dict[str, Any]:
    """Return a realistic Apify Airbnb actor item dict."""
    return {
        "id": listing_id,
        "url": f"https://www.airbnb.com/rooms/{listing_id}",
        "name": "Cozy Studio in the Heart of Paris",
        "description": "A wonderful place to stay.",
        "pricing": {
            "rate": {
                "amount": 85,
                "amountFormatted": "$85",
                "currency": "USD",
                "qualifier": "per night",
            }
        },
        "lat": 48.8566,
        "lng": 2.3522,
        "city": "Paris",
        "country": "France",
        "neighbourhood": "Le Marais",
        "bedrooms": 1,
        "bathrooms": 1.0,
        "personCapacity": 2,
        "amenities": ["WiFi", "Kitchen", "Air conditioning"],
        "starRating": 4.87,
        "reviewsCount": 156,
        "host": {
            "id": "host-99",
            "name": "Marie",
            "isSuperHost": True,
        },
    }


def _curious_coder_payload(listing_id: str = "33166539") -> dict[str, Any]:
    """Return a listing item in the `curious_coder` actor schema."""
    return {
        "id": listing_id,
        "inputUrl": f"https://www.airbnb.com/rooms/{listing_id}",
        "title": "Sunny apartment in Buenos Aires",
        "description": "Bright apartment close to the subway.",
        "location": {
            "latitude": -34.62743,
            "longitude": -58.42722,
            "address": "Parque Chacabuco, Buenos Aires, Argentina",
            "description": "Parque Chacabuco",
        },
        "maxGuestCapacity": 3,
        "amenities": [
            {"title": "Wifi", "available": True},
            {"title": "Kitchen", "available": True},
            {"title": "Hot water", "available": False},
        ],
        "starRating": 5,
        "reviewsCount": 3,
        "hostDetails": {
            "name": "Juan Andres",
            "isSuperhost": True,
        },
    }


# ---------------------------------------------------------------------------
# ApifyClient
# ---------------------------------------------------------------------------


class TestApifyClientSuccess:
    @pytest.mark.asyncio
    async def test_returns_items_on_200(self):
        items = [{"id": "1", "name": "Listing A"}]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = items

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = ApifyClient(api_token="tok", actor_id="usr~act")
            result = await client.run_and_get_items({"startUrls": []})

        assert result == items

    @pytest.mark.asyncio
    async def test_returns_items_on_201(self):
        items = [{"id": "1", "name": "Listing A"}]
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = items

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = ApifyClient(api_token="tok", actor_id="usr~act")
            result = await client.run_and_get_items({"urls": ["https://www.airbnb.com/rooms/1"]})

        assert result == items

    @pytest.mark.asyncio
    async def test_passes_token_as_auth_header(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = ApifyClient(api_token="my-token", actor_id="usr~act")
            await client.run_and_get_items({})

        call_kwargs = mock_client.post.call_args
        assert call_kwargs.kwargs["headers"]["Authorization"] == "Bearer my-token"

    @pytest.mark.asyncio
    async def test_actor_id_in_url(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = ApifyClient(api_token="tok", actor_id="dtrungtin~airbnb-scraper")
            await client.run_and_get_items({})

        called_url = mock_client.post.call_args.args[0]
        assert "dtrungtin~airbnb-scraper" in called_url


class TestApifyClientErrors:
    @pytest.mark.asyncio
    async def test_raises_apify_error_on_non_200(self):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = ApifyClient(api_token="tok", actor_id="usr~act")
            with pytest.raises(ApifyError, match="400"):
                await client.run_and_get_items({})

    @pytest.mark.asyncio
    async def test_raises_apify_error_on_non_list_body(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}  # dict, not list

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = ApifyClient(api_token="tok", actor_id="usr~act")
            with pytest.raises(ApifyError, match="Unexpected"):
                await client.run_and_get_items({})

    @pytest.mark.asyncio
    async def test_raises_apify_error_on_500(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = ApifyClient(api_token="tok", actor_id="usr~act")
            with pytest.raises(ApifyError, match="500"):
                await client.run_and_get_items({})


# ---------------------------------------------------------------------------
# AirbnbAdapter.fetch — integration with ApifyClient
# ---------------------------------------------------------------------------


class TestAirbnbAdapterFetch:
    _URL = "https://www.airbnb.com/rooms/12345"

    def _adapter(self) -> AirbnbAdapter:
        return AirbnbAdapter(settings=_make_settings())

    @pytest.mark.asyncio
    async def test_fetch_returns_adapter_result(self):
        payload = _full_airbnb_payload("12345")
        adapter = self._adapter()

        with patch.object(ApifyClient, "run_and_get_items", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = [payload]
            result = await adapter.fetch(self._URL)

        assert isinstance(result, AdapterResult)
        assert isinstance(result.listing, NormalizedListing)
        assert result.listing.provider == ListingProvider.AIRBNB
        assert result.listing.source_url == self._URL
        assert result.listing.source_id == "12345"
        assert result.listing.title == "Cozy Studio in the Heart of Paris"

    @pytest.mark.asyncio
    async def test_fetch_raw_contains_original_payload(self):
        payload = _full_airbnb_payload("12345")
        adapter = self._adapter()

        with patch.object(ApifyClient, "run_and_get_items", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = [payload]
            result = await adapter.fetch(self._URL)

        assert result.raw == payload

    @pytest.mark.asyncio
    async def test_fetch_passes_url_in_actor_input(self):
        payload = _full_airbnb_payload("12345")
        adapter = self._adapter()

        with patch.object(ApifyClient, "run_and_get_items", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = [payload]
            await adapter.fetch(self._URL)

        call_input = mock_run.call_args.args[0]
        assert call_input["startUrls"][0]["url"] == self._URL

    @pytest.mark.asyncio
    async def test_fetch_uses_actor_specific_input_for_curious_coder(self):
        settings = _make_settings(apify_airbnb_actor_id="curious_coder~airbnb-scraper")
        adapter = AirbnbAdapter(settings=settings)

        with patch.object(ApifyClient, "run_and_get_items", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = [_curious_coder_payload()]
            await adapter.fetch(self._URL)

        call_input = mock_run.call_args.args[0]
        assert call_input["urls"] == [self._URL]
        assert call_input["scrapeReviews"] is True

    @pytest.mark.asyncio
    async def test_fetch_raises_value_error_on_empty_dataset(self):
        adapter = self._adapter()

        with patch.object(ApifyClient, "run_and_get_items", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = []
            with pytest.raises(ValueError, match="empty dataset"):
                await adapter.fetch(self._URL)

    @pytest.mark.asyncio
    async def test_fetch_propagates_apify_error(self):
        adapter = self._adapter()

        with patch.object(ApifyClient, "run_and_get_items", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = ApifyError("actor failed")
            with pytest.raises(ApifyError, match="actor failed"):
                await adapter.fetch(self._URL)

    @pytest.mark.asyncio
    async def test_fetch_uses_settings_actor_id(self):
        settings = _make_settings(apify_airbnb_actor_id="custom~actor")
        adapter = AirbnbAdapter(settings=settings)

        mock_instance = MagicMock()
        mock_instance.run_and_get_items = AsyncMock(
            return_value=[_full_airbnb_payload()]
        )

        with patch("src.adapters.airbnb.ApifyClient", return_value=mock_instance) as mock_cls:
            await adapter.fetch(self._URL)

        _, init_kwargs = mock_cls.call_args
        assert init_kwargs.get("actor_id") == "custom~actor"


# ---------------------------------------------------------------------------
# _normalize — field mapping
# ---------------------------------------------------------------------------


class TestNormalize:
    _URL = "https://www.airbnb.com/rooms/12345"

    def test_full_payload_maps_all_fields(self):
        listing = _normalize(self._URL, _full_airbnb_payload("12345"))

        assert listing.provider == ListingProvider.AIRBNB
        assert listing.source_url == self._URL
        assert listing.source_id == "12345"
        assert listing.title == "Cozy Studio in the Heart of Paris"
        assert listing.description == "A wonderful place to stay."

        assert listing.price is not None
        assert listing.price.amount == Decimal("85")
        assert listing.price.currency == "USD"
        assert listing.price.period == "night"

        assert listing.location.latitude == 48.8566
        assert listing.location.longitude == 2.3522
        assert listing.location.city == "Paris"
        assert listing.location.country == "France"
        assert listing.location.neighbourhood == "Le Marais"

        assert listing.bedrooms == 1
        assert listing.bathrooms == 1.0
        assert listing.max_guests == 2
        assert listing.amenities == ["WiFi", "Kitchen", "Air conditioning"]
        assert listing.rating == pytest.approx(4.87)
        assert listing.review_count == 156
        assert listing.host_name == "Marie"
        assert listing.host_is_superhost is True

    def test_minimal_payload_falls_back_gracefully(self):
        listing = _normalize(self._URL, {"name": "Tiny Room"})

        assert listing.title == "Tiny Room"
        assert listing.source_id == "12345"  # extracted from URL
        assert listing.price is None
        assert listing.location.latitude is None
        assert listing.amenities == []
        assert listing.host_name is None
        assert listing.host_is_superhost is None

    def test_source_id_falls_back_to_url_when_missing_from_payload(self):
        listing = _normalize(self._URL, {"name": "Test"})
        assert listing.source_id == "12345"

    def test_source_id_prefers_payload_id_over_url(self):
        listing = _normalize(self._URL, {"id": "99999", "name": "Test"})
        assert listing.source_id == "99999"

    def test_room_id_field_accepted_as_source_id(self):
        listing = _normalize(self._URL, {"roomId": "77777", "name": "Test"})
        assert listing.source_id == "77777"

    def test_price_missing_when_pricing_absent(self):
        listing = _normalize(self._URL, {"name": "Test"})
        assert listing.price is None

    def test_price_missing_when_rate_amount_absent(self):
        listing = _normalize(self._URL, {"name": "Test", "pricing": {"rate": {}}})
        assert listing.price is None

    def test_amenities_empty_when_not_a_list(self):
        listing = _normalize(self._URL, {"name": "Test", "amenities": "WiFi"})
        assert listing.amenities == []

    def test_host_superhost_false_mapped(self):
        payload = {**_full_airbnb_payload(), "host": {"name": "Bob", "isSuperHost": False}}
        listing = _normalize(self._URL, payload)
        assert listing.host_is_superhost is False

    def test_alt_location_fields_accepted(self):
        payload = {
            "name": "Test",
            "latitude": 51.5,
            "longitude": -0.12,
            "countryCode": "GB",
        }
        listing = _normalize(self._URL, payload)
        assert listing.location.latitude == 51.5
        assert listing.location.longitude == -0.12
        assert listing.location.country == "GB"

    def test_alt_review_field_accepted(self):
        payload = {**_full_airbnb_payload(), "reviewsCount": None, "reviewCount": 42}
        listing = _normalize(self._URL, payload)
        assert listing.review_count == 42

    def test_alt_rating_field_accepted(self):
        payload = {**_full_airbnb_payload(), "starRating": None, "rating": 4.5}
        listing = _normalize(self._URL, payload)
        assert listing.rating == pytest.approx(4.5)

    def test_alt_title_field_accepted(self):
        listing = _normalize(self._URL, {"title": "Alt Title"})
        assert listing.title == "Alt Title"

    def test_person_capacity_maps_to_max_guests(self):
        payload = {"name": "Test", "personCapacity": 4}
        listing = _normalize(self._URL, payload)
        assert listing.max_guests == 4

    def test_curious_coder_payload_maps_expected_fields(self):
        listing = _normalize(self._URL, _curious_coder_payload())
        assert listing.title == "Sunny apartment in Buenos Aires"
        assert listing.location.latitude == pytest.approx(-34.62743)
        assert listing.location.longitude == pytest.approx(-58.42722)
        assert listing.location.address == "Parque Chacabuco, Buenos Aires, Argentina"
        assert listing.location.neighbourhood == "Parque Chacabuco"
        assert listing.max_guests == 3
        assert listing.amenities == ["Wifi", "Kitchen"]
        assert listing.host_name == "Juan Andres"
        assert listing.host_is_superhost is True

    def test_max_guests_field_accepted(self):
        payload = {"name": "Test", "maxGuests": 6}
        listing = _normalize(self._URL, payload)
        assert listing.max_guests == 6

    # ------------------------------------------------------------------
    # Zero-value preservation (regression for or-based fallback bug)
    # ------------------------------------------------------------------

    def test_zero_lat_lng_preserved(self):
        """lat=0/lng=0 are valid coordinates and must not fall through to None."""
        payload = {"name": "Test", "lat": 0.0, "lng": 0.0}
        listing = _normalize(self._URL, payload)
        assert listing.location.latitude == 0.0
        assert listing.location.longitude == 0.0

    def test_zero_lat_lng_alt_fields_preserved(self):
        """latitude=0/longitude=0 alternate field names are also preserved."""
        payload = {"name": "Test", "latitude": 0.0, "longitude": 0.0}
        listing = _normalize(self._URL, payload)
        assert listing.location.latitude == 0.0
        assert listing.location.longitude == 0.0

    def test_zero_review_count_preserved(self):
        """review_count=0 is valid for new listings and must not be dropped."""
        payload = {**_full_airbnb_payload(), "reviewsCount": 0, "reviewCount": 99}
        listing = _normalize(self._URL, payload)
        assert listing.review_count == 0

    def test_zero_review_count_alt_field_preserved(self):
        payload = {"name": "Test", "reviewsCount": None, "reviewCount": 0}
        listing = _normalize(self._URL, payload)
        # reviewsCount is None → skipped; reviewCount=0 is valid and preserved
        assert listing.review_count == 0

    def test_zero_max_guests_preserved(self):
        """personCapacity=0 must be preserved rather than falling to maxGuests."""
        payload = {"name": "Test", "personCapacity": 0, "maxGuests": 4}
        listing = _normalize(self._URL, payload)
        assert listing.max_guests == 0

    def test_zero_rating_preserved(self):
        """starRating=0 must be preserved rather than falling to rating."""
        payload = {"name": "Test", "starRating": 0.0, "rating": 4.5}
        listing = _normalize(self._URL, payload)
        assert listing.rating == pytest.approx(0.0)


class TestBuildActorInput:
    def test_default_actor_uses_start_urls_contract(self):
        payload = _build_actor_input(
            "https://www.airbnb.com/rooms/12345",
            "other~actor",
        )
        assert payload == {
            "startUrls": [{"url": "https://www.airbnb.com/rooms/12345"}],
            "maxListings": 1,
        }

    def test_curious_coder_actor_uses_urls_contract(self):
        payload = _build_actor_input(
            "https://www.airbnb.com/rooms/12345",
            "curious_coder~airbnb-scraper",
        )
        assert payload["urls"] == ["https://www.airbnb.com/rooms/12345"]
        assert payload["scrapeReviews"] is True
