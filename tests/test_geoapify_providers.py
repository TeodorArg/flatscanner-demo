"""Tests for the Geoapify enrichment providers.

Covers:
- GeoapifyTransportProvider: success, no-coordinates skip, API error
- GeoapifyNearbyPlacesProvider: success, no-coordinates skip, API error
- build_default_providers: returns providers when key set, empty list when absent
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.listing import ListingLocation, ListingProvider, NormalizedListing
from src.enrichment.providers import build_default_providers
from src.enrichment.providers.geoapify_nearby_places import GeoapifyNearbyPlacesProvider
from src.enrichment.providers.geoapify_transport import GeoapifyTransportProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_listing(lat=48.8566, lon=2.3522) -> NormalizedListing:
    return NormalizedListing(
        provider=ListingProvider.AIRBNB,
        source_url="https://www.airbnb.com/rooms/1",
        source_id="1",
        title="Test flat",
        location=ListingLocation(latitude=lat, longitude=lon),
    )


def _make_listing_no_coords() -> NormalizedListing:
    return NormalizedListing(
        provider=ListingProvider.AIRBNB,
        source_url="https://www.airbnb.com/rooms/2",
        source_id="2",
        title="No coords flat",
    )


def _geoapify_response(features: list) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"type": "FeatureCollection", "features": features}
    return resp


def _transport_feature(name: str, distance: float, categories: list[str]) -> dict:
    return {
        "type": "Feature",
        "properties": {
            "name": name,
            "distance": distance,
            "categories": categories,
        },
        "geometry": {"type": "Point", "coordinates": [2.35, 48.85]},
    }


def _place_feature(categories: list[str]) -> dict:
    return {
        "type": "Feature",
        "properties": {"categories": categories},
        "geometry": {"type": "Point", "coordinates": [2.35, 48.85]},
    }


# ---------------------------------------------------------------------------
# GeoapifyTransportProvider — name
# ---------------------------------------------------------------------------


class TestGeoapifyTransportProviderName:
    def test_name_is_transport(self):
        provider = GeoapifyTransportProvider(api_key="key")
        assert provider.name == "transport"


# ---------------------------------------------------------------------------
# GeoapifyTransportProvider — no coordinates
# ---------------------------------------------------------------------------


class TestGeoapifyTransportProviderNoCoords:
    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_no_coordinates(self):
        provider = GeoapifyTransportProvider(api_key="key")
        listing = _make_listing_no_coords()
        result = await provider.enrich(listing)
        assert result == {}

    @pytest.mark.asyncio
    async def test_does_not_call_api_when_no_coordinates(self):
        provider = GeoapifyTransportProvider(api_key="key")
        listing = _make_listing_no_coords()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await provider.enrich(listing)

        mock_client.get.assert_not_called()


# ---------------------------------------------------------------------------
# GeoapifyTransportProvider — success
# ---------------------------------------------------------------------------


class TestGeoapifyTransportProviderSuccess:
    @pytest.mark.asyncio
    async def test_returns_count_of_features(self):
        provider = GeoapifyTransportProvider(api_key="key")
        listing = _make_listing()
        features = [
            _transport_feature("Metro A", 120.0, ["public_transport.subway"]),
            _transport_feature("Bus 42", 200.0, ["public_transport.bus"]),
        ]
        resp = _geoapify_response(features)

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await provider.enrich(listing)

        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_nearest_name_from_first_feature(self):
        provider = GeoapifyTransportProvider(api_key="key")
        listing = _make_listing()
        features = [_transport_feature("Central Station", 80.0, ["public_transport.train"])]
        resp = _geoapify_response(features)

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await provider.enrich(listing)

        assert result["nearest_name"] == "Central Station"
        assert result["nearest_distance_m"] == 80.0

    @pytest.mark.asyncio
    async def test_categories_found_are_top_level(self):
        provider = GeoapifyTransportProvider(api_key="key")
        listing = _make_listing()
        features = [
            _transport_feature("Subway", 100.0, ["public_transport.subway"]),
            _transport_feature("Bus", 150.0, ["public_transport.bus"]),
        ]
        resp = _geoapify_response(features)

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await provider.enrich(listing)

        assert result["categories_found"] == ["public_transport"]

    @pytest.mark.asyncio
    async def test_empty_features_returns_zero_count(self):
        provider = GeoapifyTransportProvider(api_key="key")
        listing = _make_listing()
        resp = _geoapify_response([])

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await provider.enrich(listing)

        assert result["count"] == 0
        assert result["nearest_name"] is None
        assert result["nearest_distance_m"] is None
        assert result["categories_found"] == []

    @pytest.mark.asyncio
    async def test_sends_api_key_in_params(self):
        provider = GeoapifyTransportProvider(api_key="my-geoapify-key")
        listing = _make_listing()
        resp = _geoapify_response([])

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await provider.enrich(listing)

        call_kwargs = mock_client.get.call_args.kwargs
        assert call_kwargs["params"]["apiKey"] == "my-geoapify-key"

    @pytest.mark.asyncio
    async def test_filter_contains_coordinates(self):
        provider = GeoapifyTransportProvider(api_key="key", radius_m=300)
        listing = _make_listing(lat=51.5074, lon=-0.1278)
        resp = _geoapify_response([])

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await provider.enrich(listing)

        call_kwargs = mock_client.get.call_args.kwargs
        filter_val = call_kwargs["params"]["filter"]
        assert "-0.1278" in filter_val
        assert "51.5074" in filter_val
        assert "300" in filter_val


# ---------------------------------------------------------------------------
# GeoapifyTransportProvider — API error
# ---------------------------------------------------------------------------


class TestGeoapifyTransportProviderError:
    @pytest.mark.asyncio
    async def test_raises_on_non_200_response(self):
        provider = GeoapifyTransportProvider(api_key="key")
        listing = _make_listing()

        error_resp = MagicMock()
        error_resp.status_code = 401
        error_resp.text = "Unauthorized"

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=error_resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(RuntimeError, match="401"):
                await provider.enrich(listing)


# ---------------------------------------------------------------------------
# GeoapifyNearbyPlacesProvider — name
# ---------------------------------------------------------------------------


class TestGeoapifyNearbyPlacesProviderName:
    def test_name_is_nearby_places(self):
        provider = GeoapifyNearbyPlacesProvider(api_key="key")
        assert provider.name == "nearby_places"


# ---------------------------------------------------------------------------
# GeoapifyNearbyPlacesProvider — no coordinates
# ---------------------------------------------------------------------------


class TestGeoapifyNearbyPlacesProviderNoCoords:
    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_no_coordinates(self):
        provider = GeoapifyNearbyPlacesProvider(api_key="key")
        listing = _make_listing_no_coords()
        result = await provider.enrich(listing)
        assert result == {}

    @pytest.mark.asyncio
    async def test_does_not_call_api_when_no_coordinates(self):
        provider = GeoapifyNearbyPlacesProvider(api_key="key")
        listing = _make_listing_no_coords()

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await provider.enrich(listing)

        mock_client.get.assert_not_called()


# ---------------------------------------------------------------------------
# GeoapifyNearbyPlacesProvider — success
# ---------------------------------------------------------------------------


class TestGeoapifyNearbyPlacesProviderSuccess:
    @pytest.mark.asyncio
    async def test_returns_total_count(self):
        provider = GeoapifyNearbyPlacesProvider(api_key="key")
        listing = _make_listing()
        features = [
            _place_feature(["commercial.supermarket"]),
            _place_feature(["catering.restaurant"]),
            _place_feature(["catering.cafe"]),
        ]
        resp = _geoapify_response(features)

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await provider.enrich(listing)

        assert result["count"] == 3

    @pytest.mark.asyncio
    async def test_groups_by_friendly_category_label(self):
        provider = GeoapifyNearbyPlacesProvider(api_key="key")
        listing = _make_listing()
        features = [
            _place_feature(["commercial.supermarket"]),
            _place_feature(["commercial.convenience"]),
            _place_feature(["catering.restaurant"]),
            _place_feature(["leisure.park"]),
        ]
        resp = _geoapify_response(features)

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await provider.enrich(listing)

        by_cat = result["by_category"]
        assert by_cat["shops"] == 2
        assert by_cat["restaurants_cafes"] == 1
        assert by_cat["parks"] == 1

    @pytest.mark.asyncio
    async def test_empty_features_returns_zero_count(self):
        provider = GeoapifyNearbyPlacesProvider(api_key="key")
        listing = _make_listing()
        resp = _geoapify_response([])

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await provider.enrich(listing)

        assert result["count"] == 0
        assert result["by_category"] == {}

    @pytest.mark.asyncio
    async def test_sends_api_key_in_params(self):
        provider = GeoapifyNearbyPlacesProvider(api_key="places-key")
        listing = _make_listing()
        resp = _geoapify_response([])

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await provider.enrich(listing)

        call_kwargs = mock_client.get.call_args.kwargs
        assert call_kwargs["params"]["apiKey"] == "places-key"

    @pytest.mark.asyncio
    async def test_classifies_by_known_category_regardless_of_position(self):
        """Regression: known category not at categories[0] must still be classified."""
        provider = GeoapifyNearbyPlacesProvider(api_key="key")
        listing = _make_listing()
        # The known category "commercial.supermarket" appears second; "building.retail"
        # is first.  The provider must scan past the unknown top-level and classify
        # the feature as "shops".
        features = [
            _place_feature(["building.retail", "commercial.supermarket"]),
        ]
        resp = _geoapify_response(features)

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await provider.enrich(listing)

        assert result["by_category"].get("shops") == 1


# ---------------------------------------------------------------------------
# GeoapifyNearbyPlacesProvider — API error
# ---------------------------------------------------------------------------


class TestGeoapifyNearbyPlacesProviderError:
    @pytest.mark.asyncio
    async def test_raises_on_non_200_response(self):
        provider = GeoapifyNearbyPlacesProvider(api_key="key")
        listing = _make_listing()

        error_resp = MagicMock()
        error_resp.status_code = 403
        error_resp.text = "Forbidden"

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=error_resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            with pytest.raises(RuntimeError, match="403"):
                await provider.enrich(listing)


# ---------------------------------------------------------------------------
# build_default_providers
# ---------------------------------------------------------------------------


class TestBuildDefaultProviders:
    def _make_settings(self, geoapify_api_key: str = ""):
        from src.app.config import Settings

        return Settings(
            app_env="testing",
            geoapify_api_key=geoapify_api_key,
        )

    def test_returns_empty_list_when_no_key(self):
        settings = self._make_settings(geoapify_api_key="")
        providers = build_default_providers(settings)
        assert providers == []

    def test_returns_two_providers_when_key_set(self):
        settings = self._make_settings(geoapify_api_key="geo-key-123")
        providers = build_default_providers(settings)
        assert len(providers) == 2

    def test_first_provider_is_transport(self):
        settings = self._make_settings(geoapify_api_key="geo-key-123")
        providers = build_default_providers(settings)
        assert providers[0].name == "transport"

    def test_second_provider_is_nearby_places(self):
        settings = self._make_settings(geoapify_api_key="geo-key-123")
        providers = build_default_providers(settings)
        assert providers[1].name == "nearby_places"

    def test_providers_are_correct_types(self):
        settings = self._make_settings(geoapify_api_key="geo-key-123")
        providers = build_default_providers(settings)
        assert isinstance(providers[0], GeoapifyTransportProvider)
        assert isinstance(providers[1], GeoapifyNearbyPlacesProvider)
