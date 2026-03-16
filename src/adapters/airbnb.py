"""Airbnb listing adapter.

Handles Airbnb URL recognition, Apify-backed data retrieval, and
normalisation of raw Airbnb payloads into ``NormalizedListing``.

Recognised URL patterns
-----------------------
- ``airbnb.com/rooms/<id>`` and ``www.airbnb.com/rooms/<id>``
- Localised Airbnb domains from the supported TLD allowlist
  (e.g. ``airbnb.co.uk``, ``www.airbnb.de``, ``www.airbnb.com.au``)
  — listing-path restriction ``/rooms/<id>`` applies to all
- ``abnb.me/<code>`` and ``www.abnb.me/<code>``  (Airbnb short/share links)

Only ``http`` and ``https`` schemes are accepted.
Non-listing Airbnb pages (help, search, profiles, …) are not recognised.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from src.adapters.apify_client import ApifyClient, ApifyError
from src.adapters.base import ListingAdapter
from src.domain.listing import (
    ListingLocation,
    ListingProvider,
    NormalizedListing,
    PriceInfo,
)

if TYPE_CHECKING:
    from src.app.config import Settings

# Explicit allowlist of TLD suffixes for Airbnb domains supported in this MVP.
# Hosts are matched as (www.)?airbnb.<tld>.  Any domain not in this set is
# rejected.  This is intentionally conservative: add new entries as markets
# are validated.
_AIRBNB_SUPPORTED_TLDS: frozenset[str] = frozenset({
    "com",       # US (primary)
    "ca",        # Canada
    "co.uk",     # United Kingdom
    "com.au",    # Australia
    "co.nz",     # New Zealand
    "co.in",     # India
    "de",        # Germany
    "fr",        # France
    "es",        # Spain
    "it",        # Italy
    "pt",        # Portugal
    "nl",        # Netherlands
    "pl",        # Poland
    "se",        # Sweden
    "no",        # Norway
    "dk",        # Denmark
    "fi",        # Finland
    "at",        # Austria
    "ch",        # Switzerland
    "be",        # Belgium
    "ie",        # Ireland
    "gr",        # Greece
    "com.br",    # Brazil
    "com.mx",    # Mexico
    "com.ar",    # Argentina
    "com.co",    # Colombia
    "com.sg",    # Singapore
    "com.hk",    # Hong Kong
    "co.kr",     # South Korea
    "co.id",     # Indonesia
    "com.my",    # Malaysia
})

# Requires exactly /rooms/<id> with an optional trailing slash.
# Rejects bare /rooms/ and any extra path segments like /rooms/123/photos.
_AIRBNB_LISTING_PATH_RE = re.compile(r"^/rooms/([^/?#\s]+)/?$", re.IGNORECASE)


def _is_airbnb_host(host: str) -> bool:
    """Return True if *host* is a known Airbnb domain from the supported allowlist.

    Only the bare domain (airbnb.<tld>) and its www. subdomain are accepted;
    other subdomains (e.g. fr.airbnb.com) are not matched to keep the check
    narrow for the MVP.
    """
    h = host.lower()
    if h.startswith("www."):
        h = h[4:]
    if not h.startswith("airbnb."):
        return False
    tld = h[len("airbnb."):]
    return tld in _AIRBNB_SUPPORTED_TLDS


def _extract_listing_id_from_url(url: str) -> str:
    """Return the Airbnb listing ID embedded in *url*, or an empty string."""
    try:
        path = urlparse(url).path
        match = _AIRBNB_LISTING_PATH_RE.match(path)
        if match:
            return match.group(1).rstrip("/")
    except Exception:
        pass
    return ""


def _first_non_none(mapping: dict[str, Any], *keys: str) -> Any:
    """Return the value of the first *key* in *mapping* whose value is not ``None``.

    Unlike ``mapping.get(k1) or mapping.get(k2)``, this correctly handles
    zero-valued numeric fields: a key whose value is ``0`` or ``0.0`` is
    returned rather than falling through to the next candidate key.
    Returns ``None`` if all keys are absent or all present values are ``None``.
    """
    for key in keys:
        val = mapping.get(key)
        if val is not None:
            return val
    return None


def _normalize(url: str, raw: dict[str, Any]) -> NormalizedListing:
    """Map a raw Apify Airbnb actor item to a ``NormalizedListing``.

    The function is deliberately defensive: all fields are optional in the
    raw payload and are silently skipped when absent or of an unexpected type.
    Only ``title`` is required; an empty string is used as fallback so the
    domain model constraint is always satisfied.

    Parameters
    ----------
    url:
        The original listing URL submitted by the user (used as ``source_url``
        and as the fallback source of the listing ID).
    raw:
        A single item dict from the Apify actor dataset.
    """
    # --- source_id -----------------------------------------------------------
    # Prefer the explicit id field in the payload; fall back to URL parsing.
    source_id = str(raw.get("id") or raw.get("roomId") or "").strip()
    if not source_id:
        source_id = _extract_listing_id_from_url(url)

    # --- price ---------------------------------------------------------------
    price: PriceInfo | None = None
    pricing = raw.get("pricing")
    if isinstance(pricing, dict):
        rate = pricing.get("rate")
        if isinstance(rate, dict) and rate.get("amount") is not None:
            try:
                price = PriceInfo(
                    amount=Decimal(str(rate["amount"])),
                    currency=str(rate.get("currency") or "USD"),
                    period="night",
                )
            except Exception:
                pass

    # --- location ------------------------------------------------------------
    def _float_or_none(val: Any) -> float | None:
        try:
            return float(val) if val is not None else None
        except (TypeError, ValueError):
            return None

    # Use _first_non_none so that zero-valued coordinates (e.g. lat=0, lng=0)
    # are preserved rather than treated as falsy and silently dropped.
    location = ListingLocation(
        latitude=_float_or_none(_first_non_none(raw, "lat", "latitude")),
        longitude=_float_or_none(_first_non_none(raw, "lng", "longitude")),
        address=raw.get("address") or None,
        city=raw.get("city") or None,
        country=raw.get("country") or raw.get("countryCode") or None,
        neighbourhood=raw.get("neighbourhood") or None,
    )

    # --- amenities -----------------------------------------------------------
    raw_amenities = raw.get("amenities")
    amenities: list[str] = []
    if isinstance(raw_amenities, list):
        amenities = [str(a) for a in raw_amenities if a]

    # --- host ----------------------------------------------------------------
    host = raw.get("host")
    host_name: str | None = None
    host_is_superhost: bool | None = None
    if isinstance(host, dict):
        host_name = host.get("name") or None
        raw_superhost = host.get("isSuperHost")
        if raw_superhost is not None:
            host_is_superhost = bool(raw_superhost)

    # --- numeric helpers -----------------------------------------------------
    def _int_or_none(val: Any) -> int | None:
        try:
            return int(val) if val is not None else None
        except (TypeError, ValueError):
            return None

    def _rating_or_none(val: Any) -> float | None:
        try:
            return float(val) if val is not None else None
        except (TypeError, ValueError):
            return None

    return NormalizedListing(
        provider=ListingProvider.AIRBNB,
        source_url=url,
        source_id=source_id,
        title=str(raw.get("name") or raw.get("title") or ""),
        description=raw.get("description") or None,
        location=location,
        price=price,
        bedrooms=_int_or_none(raw.get("bedrooms")),
        bathrooms=_rating_or_none(raw.get("bathrooms")),
        # _first_non_none preserves zero (e.g. personCapacity=0 on a listing
        # pending capacity configuration) instead of falling through.
        max_guests=_int_or_none(
            _first_non_none(raw, "personCapacity", "maxGuests")
        ),
        amenities=amenities,
        rating=_rating_or_none(_first_non_none(raw, "starRating", "rating")),
        # review_count=0 is valid for newly-listed properties.
        review_count=_int_or_none(
            _first_non_none(raw, "reviewsCount", "reviewCount")
        ),
        host_name=host_name,
        host_is_superhost=host_is_superhost,
    )


class AirbnbAdapter(ListingAdapter):
    """Adapter for Airbnb listing URLs.

    Fetches listing data via the Apify Airbnb scraper actor and normalises the
    raw payload into a ``NormalizedListing``.

    Parameters
    ----------
    settings:
        Application settings.  When *None* (the default), settings are loaded
        lazily from the environment on the first ``fetch`` call.  Pass an
        explicit ``Settings`` instance in tests to avoid touching environment
        variables.
    """

    provider = ListingProvider.AIRBNB

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings

    def _get_settings(self) -> Settings:
        if self._settings is not None:
            return self._settings
        from src.app.config import get_settings  # deferred to avoid import cycles
        return get_settings()

    def supports_url(self, url: str) -> bool:
        """Return True if *url* is a recognised Airbnb listing URL."""
        try:
            parsed = urlparse(url)
            scheme = (parsed.scheme or "").lower()
            host = parsed.hostname or ""
            path = parsed.path
        except Exception:
            return False

        if scheme not in ("http", "https"):
            return False

        if host == "abnb.me" or host.endswith(".abnb.me"):
            # Require a non-empty path segment (bare abnb.me/ with no code is not
            # a listing).
            return bool(path) and path != "/"

        if _is_airbnb_host(host):
            return bool(_AIRBNB_LISTING_PATH_RE.match(path))

        return False

    async def fetch(self, url: str) -> NormalizedListing:
        """Fetch the Airbnb listing at *url* via Apify and return a normalised record.

        Parameters
        ----------
        url:
            A recognised Airbnb listing URL (see ``supports_url``).

        Returns
        -------
        NormalizedListing
            Provider-agnostic listing representation.

        Raises
        ------
        ApifyError
            If the Apify actor run fails or returns an unexpected response.
        ValueError
            If the actor returns an empty dataset (listing not found or
            scraping blocked).
        httpx.TimeoutException
            If the actor does not finish within the configured timeout.
        """
        settings = self._get_settings()
        client = ApifyClient(
            api_token=settings.apify_api_token,
            actor_id=settings.apify_airbnb_actor_id,
        )
        items = await client.run_and_get_items(
            {"startUrls": [{"url": url}], "maxListings": 1}
        )
        if not items:
            raise ValueError(
                f"Apify returned an empty dataset for URL: {url!r}. "
                "The listing may not exist or scraping may have been blocked."
            )
        return _normalize(url, items[0])
