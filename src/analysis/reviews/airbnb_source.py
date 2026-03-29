"""Airbnb review source backed by one listing-payload actor.

Runs a configurable Airbnb listing actor and normalizes embedded ``reviews[]``
from the returned listing payload.
"""

from __future__ import annotations

from typing import Any

from src.adapters.apify_client import ApifyClient
from src.analysis.reviews.normalizers.airbnb import AirbnbReviewNormalizer
from src.domain.review_corpus import ReviewExtractionResult

_DEFAULT_ACTOR_ID = "curious_coder~airbnb-scraper"


class AirbnbReviewSource:
    """Fetch and normalize Airbnb reviews from a listing payload actor."""

    def __init__(
        self,
        api_token: str,
        *,
        actor_id: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self._actor_id = actor_id or _DEFAULT_ACTOR_ID
        self._client = ApifyClient(
            api_token=api_token,
            actor_id=self._actor_id,
            timeout=timeout,
        )
        self._normalizer = AirbnbReviewNormalizer()

    @property
    def actor_id(self) -> str:
        return self._actor_id

    async def fetch(self, listing_url: str, listing: Any) -> ReviewExtractionResult:
        """Fetch reviews for *listing_url* and normalize them immediately."""
        items = await self._client.run_and_get_items(self._build_input(listing_url))
        payload: dict[str, Any] = items[0] if items and isinstance(items[0], dict) else {}
        return self._normalizer.normalize(payload, listing)

    @staticmethod
    def _build_input(listing_url: str) -> dict[str, Any]:
        return {
            "urls": [listing_url],
            "currency": "USD",
            "scrapeAvailability": False,
            "scrapeDetail": False,
            "scrapeReviews": True,
        }
