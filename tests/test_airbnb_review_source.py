"""Tests for the Airbnb listing-payload review source."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.analysis.reviews.airbnb_source import AirbnbReviewSource
from src.domain.listing import ListingProvider, NormalizedListing

_LISTING_URL = "https://www.airbnb.com/rooms/12345678"


def _listing() -> NormalizedListing:
    return NormalizedListing(
        provider=ListingProvider.AIRBNB,
        source_url=_LISTING_URL,
        source_id="12345678",
        title="Test Listing",
        review_count=14,
        rating=4.9,
    )


_CURIOUS_ITEMS = [
    {
        "reviews": [
            {
                "id": "review-1",
                "reviewer": {"firstName": "Alice", "location": "New York"},
                "createdAt": "2024-03-15",
                "rating": 5,
                "comments": "Great place, very clean!",
                "response": None,
            }
        ],
        "reviewsCount": 14,
        "starRating": 4.9,
    }
]


class TestAirbnbReviewSourceInit:
    def test_default_actor_uses_curious_coder(self):
        with patch("src.analysis.reviews.airbnb_source.ApifyClient") as MockClient:
            source = AirbnbReviewSource(api_token="tok")
            assert source.actor_id == "curious_coder~airbnb-scraper"
            MockClient.assert_called_once_with(
                api_token="tok",
                actor_id="curious_coder~airbnb-scraper",
                timeout=120.0,
            )

    def test_custom_actor_id_overrides_strategy_default(self):
        with patch("src.analysis.reviews.airbnb_source.ApifyClient") as MockClient:
            source = AirbnbReviewSource(
                api_token="tok",
                actor_id="custom~actor",
            )
            assert source.actor_id == "custom~actor"
            MockClient.assert_called_once_with(
                api_token="tok",
                actor_id="custom~actor",
                timeout=120.0,
            )


class TestAirbnbReviewSourceFetch:
    @pytest.mark.asyncio
    async def test_curious_source_sends_listing_payload_input(self):
        source = AirbnbReviewSource(api_token="tok")
        source._client.run_and_get_items = AsyncMock(return_value=_CURIOUS_ITEMS)

        extraction = await source.fetch(_LISTING_URL, _listing())

        source._client.run_and_get_items.assert_awaited_once_with(
            {
                "urls": [_LISTING_URL],
                "currency": "USD",
                "scrapeAvailability": False,
                "scrapeDetail": False,
                "scrapeReviews": True,
            }
        )
        assert extraction.corpus.total_review_count == 14
        assert len(extraction.corpus.comments) == 1
        assert extraction.corpus.comments[0].comment_text == "Great place, very clean!"

    @pytest.mark.asyncio
    async def test_empty_actor_output_returns_empty_extraction(self):
        source = AirbnbReviewSource(api_token="tok")
        source._client.run_and_get_items = AsyncMock(return_value=[])

        extraction = await source.fetch(_LISTING_URL, _listing())

        assert extraction.corpus.total_review_count == 14
        assert extraction.corpus.comments == []
