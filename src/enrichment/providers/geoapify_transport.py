"""Geoapify Places-based public-transport enrichment provider.

Fetches nearby public transport stops (subway, train, tram, bus, ferry)
within a configurable radius of the listing coordinates using the Geoapify
Places API.

Return schema::

    {
        "count": <int>,               # stops found within radius
        "nearest_name": <str|None>,   # name of the closest stop
        "nearest_distance_m": <float|None>,
        "categories_found": [<str>],  # distinct top-level categories
    }

Returns an empty dict when the listing has no coordinates (no-op, not a
failure).  Raises on API errors — the runner records these as failures and
continues without blocking the pipeline.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.domain.listing import NormalizedListing

logger = logging.getLogger(__name__)

_GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"

_TRANSPORT_CATEGORIES = ",".join([
    "public_transport.subway",
    "public_transport.train",
    "public_transport.tram",
    "public_transport.bus",
    "public_transport.ferry",
])


class GeoapifyTransportProvider:
    """Enriches a listing with nearby public transport data from Geoapify."""

    def __init__(self, api_key: str, radius_m: int = 500) -> None:
        self._api_key = api_key
        self._radius_m = radius_m

    @property
    def name(self) -> str:
        return "transport"

    async def enrich(self, listing: NormalizedListing) -> dict[str, Any]:
        lat = listing.location.latitude
        lon = listing.location.longitude
        if lat is None or lon is None:
            logger.debug(
                "Skipping transport enrichment for listing %s: no coordinates",
                listing.id,
            )
            return {}

        params = {
            "categories": _TRANSPORT_CATEGORIES,
            "filter": f"circle:{lon},{lat},{self._radius_m}",
            "bias": f"proximity:{lon},{lat}",
            "limit": 10,
            "apiKey": self._api_key,
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(_GEOAPIFY_PLACES_URL, params=params)

        if not response.is_success:
            raise RuntimeError(
                f"Geoapify Places API returned {response.status_code}: "
                f"{response.text[:200]}"
            )

        data = response.json()
        features = data.get("features", [])

        result: dict[str, Any] = {"count": len(features)}

        if features:
            first_props = features[0].get("properties", {})
            result["nearest_name"] = (
                first_props.get("name") or first_props.get("address_line1")
            )
            result["nearest_distance_m"] = first_props.get("distance")

            categories: set[str] = set()
            for feat in features:
                for cat in feat.get("properties", {}).get("categories", []):
                    top = cat.split(".")[0] if "." in cat else cat
                    categories.add(top)
            result["categories_found"] = sorted(categories)
        else:
            result["nearest_name"] = None
            result["nearest_distance_m"] = None
            result["categories_found"] = []

        return result
