"""Geoapify Places-based nearby-places enrichment provider.

Fetches nearby POIs (supermarkets, restaurants, cafes, parks, pharmacies)
within a configurable radius of the listing coordinates using the Geoapify
Places API.

Return schema::

    {
        "count": <int>,                   # total POIs found
        "by_category": {<label>: <int>},  # count per friendly category label
    }

Returns an empty dict when the listing has no coordinates (no-op, not a
failure).  Raises on API errors — the runner records these as failures and
continues without blocking the pipeline.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

import httpx

from src.domain.listing import NormalizedListing

logger = logging.getLogger(__name__)

_GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"

_NEARBY_CATEGORIES = ",".join([
    "commercial.supermarket",
    "commercial.convenience",
    "catering.restaurant",
    "catering.cafe",
    "leisure.park",
    "healthcare.pharmacy",
])

# Maps Geoapify top-level category → human-friendly label used in enrichment output.
_CATEGORY_LABELS: dict[str, str] = {
    "commercial": "shops",
    "catering": "restaurants_cafes",
    "leisure": "parks",
    "healthcare": "pharmacies",
}


class GeoapifyNearbyPlacesProvider:
    """Enriches a listing with nearby places data from Geoapify."""

    def __init__(self, api_key: str, radius_m: int = 500) -> None:
        self._api_key = api_key
        self._radius_m = radius_m

    @property
    def name(self) -> str:
        return "nearby_places"

    async def enrich(self, listing: NormalizedListing) -> dict[str, Any]:
        lat = listing.location.latitude
        lon = listing.location.longitude
        if lat is None or lon is None:
            logger.debug(
                "Skipping nearby-places enrichment for listing %s: no coordinates",
                listing.id,
            )
            return {}

        params = {
            "categories": _NEARBY_CATEGORIES,
            "filter": f"circle:{lon},{lat},{self._radius_m}",
            "bias": f"proximity:{lon},{lat}",
            "limit": 20,
            "apiKey": self._api_key,
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(_GEOAPIFY_PLACES_URL, params=params)

        if response.status_code != 200:
            raise RuntimeError(
                f"Geoapify Places API returned {response.status_code}: "
                f"{response.text[:200]}"
            )

        data = response.json()
        features = data.get("features", [])

        counts: Counter[str] = Counter()
        for feat in features:
            cats = feat.get("properties", {}).get("categories", [])
            label: str | None = None
            for cat in cats:
                top = cat.split(".")[0] if "." in cat else cat
                if top in _CATEGORY_LABELS:
                    label = _CATEGORY_LABELS[top]
                    break
            if label is None and cats:
                # Fallback: use top-level of first category as-is
                first = cats[0]
                label = first.split(".")[0] if "." in first else first
            if label is not None:
                counts[label] += 1

        return {
            "count": len(features),
            "by_category": dict(counts),
        }
