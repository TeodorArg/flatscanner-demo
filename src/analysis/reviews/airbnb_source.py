"""Airbnb dedicated reviews source.

Fetches guest reviews for an Airbnb listing from the dedicated
``tri_angle~airbnb-reviews-scraper`` Apify actor.

Confirmed actor contract:
- Input:  ``{"startUrls": [{"url": "<listing-url>"}]}``
- Output: flat list of review items, one item per review, with fields:
  ``id``, ``language``, ``text``, ``localizedText``, ``localizedDate``,
  ``localizedReviewerLocation``, ``createdAt``, ``reviewer.firstName``,
  ``reviewee``, ``rating``, ``response``, ``reviewHighlight``, ``startUrl``.
"""

from __future__ import annotations

import logging
from typing import Any

from src.adapters.apify_client import ApifyClient

logger = logging.getLogger(__name__)

_REVIEWS_ACTOR_DEFAULT = "tri_angle~airbnb-reviews-scraper"


class AirbnbReviewSource:
    """Fetches Airbnb reviews from the dedicated tri_angle reviews actor.

    Parameters
    ----------
    api_token:
        Apify personal API token.
    actor_id:
        Reviews actor identifier in ``username~actor-name`` form.
        Defaults to ``tri_angle~airbnb-reviews-scraper``.
    timeout:
        HTTP request timeout in seconds (default 120).
    """

    def __init__(
        self,
        api_token: str,
        actor_id: str = _REVIEWS_ACTOR_DEFAULT,
        timeout: float = 120.0,
    ) -> None:
        self._client = ApifyClient(api_token=api_token, actor_id=actor_id, timeout=timeout)

    async def fetch(self, listing_url: str) -> list[dict[str, Any]]:
        """Fetch reviews for *listing_url* from the reviews actor.

        Parameters
        ----------
        listing_url:
            Full Airbnb listing URL passed as ``startUrls`` input to the actor.

        Returns
        -------
        list[dict[str, Any]]
            Flat list of raw review item dicts from the actor dataset.
            Returns an empty list when the actor returns no items.

        Raises
        ------
        ApifyError
            If the actor run fails at the HTTP level.
        httpx.TimeoutException
            If the actor does not finish within the configured timeout.
        """
        items = await self._client.run_and_get_items(
            {"startUrls": [{"url": listing_url}]}
        )
        return items
