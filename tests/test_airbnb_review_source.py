"""Tests for the dedicated Airbnb reviews source (Slice 2).

Covers:
- AirbnbReviewSource.fetch(): passes correct input to ApifyClient,
  returns items list, propagates ApifyError and timeout errors
- Default actor ID is tri_angle~airbnb-reviews-scraper
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.adapters.apify_client import ApifyError
from src.analysis.reviews.airbnb_source import AirbnbReviewSource


_LISTING_URL = "https://www.airbnb.com/rooms/12345678"

_SAMPLE_ITEMS = [
    {
        "id": "review-1",
        "language": "en",
        "text": "Great place, very clean!",
        "localizedDate": "March 2024",
        "createdAt": "2024-03-15",
        "localizedReviewerLocation": "New York",
        "reviewer": {"firstName": "Alice"},
        "rating": 5,
        "response": None,
        "reviewHighlight": None,
        "startUrl": _LISTING_URL,
    },
    {
        "id": "review-2",
        "language": "fr",
        "text": "Très bien, je recommande.",
        "localizedDate": "February 2024",
        "createdAt": "2024-02-10",
        "localizedReviewerLocation": "Paris",
        "reviewer": {"firstName": "Pierre"},
        "rating": 4,
        "response": "Merci!",
        "reviewHighlight": None,
        "startUrl": _LISTING_URL,
    },
]


class TestAirbnbReviewSourceInit:
    def test_default_actor_id(self):
        """AirbnbReviewSource passes the default actor ID to ApifyClient."""
        with patch("src.analysis.reviews.airbnb_source.ApifyClient") as MockClient:
            AirbnbReviewSource(api_token="tok")
            MockClient.assert_called_once_with(
                api_token="tok",
                actor_id="tri_angle~airbnb-reviews-scraper",
                timeout=120.0,
            )

    def test_custom_actor_id(self):
        """A custom actor_id is forwarded to ApifyClient unchanged."""
        with patch("src.analysis.reviews.airbnb_source.ApifyClient") as MockClient:
            AirbnbReviewSource(api_token="tok", actor_id="other~actor")
            MockClient.assert_called_once_with(
                api_token="tok",
                actor_id="other~actor",
                timeout=120.0,
            )

    def test_custom_timeout_passed_through(self):
        """A custom timeout is forwarded to ApifyClient unchanged."""
        with patch("src.analysis.reviews.airbnb_source.ApifyClient") as MockClient:
            AirbnbReviewSource(api_token="tok", timeout=60.0)
            MockClient.assert_called_once_with(
                api_token="tok",
                actor_id="tri_angle~airbnb-reviews-scraper",
                timeout=60.0,
            )


class TestAirbnbReviewSourceFetch:
    @pytest.mark.asyncio
    async def test_fetch_returns_items(self):
        source = AirbnbReviewSource(api_token="tok")
        source._client.run_and_get_items = AsyncMock(return_value=_SAMPLE_ITEMS)

        result = await source.fetch(_LISTING_URL)

        assert result == _SAMPLE_ITEMS

    @pytest.mark.asyncio
    async def test_fetch_sends_correct_input(self):
        source = AirbnbReviewSource(api_token="tok")
        source._client.run_and_get_items = AsyncMock(return_value=[])

        await source.fetch(_LISTING_URL)

        source._client.run_and_get_items.assert_awaited_once_with(
            {"startUrls": [{"url": _LISTING_URL}]}
        )

    @pytest.mark.asyncio
    async def test_fetch_returns_empty_list_when_actor_returns_no_items(self):
        source = AirbnbReviewSource(api_token="tok")
        source._client.run_and_get_items = AsyncMock(return_value=[])

        result = await source.fetch(_LISTING_URL)

        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_propagates_apify_error(self):
        source = AirbnbReviewSource(api_token="tok")
        source._client.run_and_get_items = AsyncMock(
            side_effect=ApifyError("actor run failed with status 500")
        )

        with pytest.raises(ApifyError, match="actor run failed"):
            await source.fetch(_LISTING_URL)

    @pytest.mark.asyncio
    async def test_fetch_propagates_timeout_error(self):
        import httpx

        source = AirbnbReviewSource(api_token="tok")
        source._client.run_and_get_items = AsyncMock(
            side_effect=httpx.TimeoutException("timed out")
        )

        with pytest.raises(httpx.TimeoutException):
            await source.fetch(_LISTING_URL)
