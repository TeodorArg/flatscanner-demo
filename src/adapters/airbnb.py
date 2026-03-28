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
from urllib.parse import parse_qs, urlparse

from src.adapters.apify_client import ApifyClient, ApifyError
from src.adapters.base import AdapterResult, ListingAdapter
from src.domain.listing import (
    ListingLocation,
    ListingProvider,
    NormalizedListing,
    PriceInfo,
)

if TYPE_CHECKING:
    from src.app.config import Settings

# Accept `airbnb.<tld>` and `airbnb.<tld>.<tld>` (optionally prefixed by `www.`).
# This removes the need for a hand-maintained market allowlist while still
# rejecting obvious lookalikes such as `airbnb.evil.com`.
_AIRBNB_HOST_RE = re.compile(
    r"^(?:www\.)?airbnb\.[a-z]{2,3}(?:\.[a-z]{2,3})?$",
    re.IGNORECASE,
)

# Requires exactly /rooms/<id> with an optional trailing slash.
# Rejects bare /rooms/ and any extra path segments like /rooms/123/photos.
_AIRBNB_LISTING_PATH_RE = re.compile(r"^/rooms/([^/?#\s]+)/?$", re.IGNORECASE)
_CURIOUS_CODER_ACTOR_IDS: frozenset[str] = frozenset({
    "curious_coder~airbnb-scraper",
})
_TRI_ANGLE_ROOMS_ACTOR_IDS: frozenset[str] = frozenset({
    # Tilde form is required by the Apify REST API; slash form returns 404.
    "tri_angle~airbnb-rooms-urls-scraper",
})


def _is_airbnb_host(host: str) -> bool:
    """Return True if *host* matches the supported Airbnb hostname shape."""
    return bool(_AIRBNB_HOST_RE.match(host.lower()))


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


def _first_present(*values: Any) -> Any:
    """Return the first value that is not ``None``."""
    for value in values:
        if value is not None:
            return value
    return None


def _period_from_qualifier(qualifier: Any) -> str:
    """Derive a price period from the tri_angle ``price.qualifier`` field.

    Returns ``'night'`` for nightly rates, ``'month'`` for monthly stays,
    ``'week'`` for weekly stays, and ``'stay'`` for any multi-night qualifier
    (e.g. ``'for 7 nights'``) where the amount is a stay total rather than a
    per-night rate.  Defaults to ``'night'`` when *qualifier* is absent or not
    a string (so undated/nightly requests are not affected); defaults to
    ``'stay'`` for any unrecognised string qualifier so unknown rates are not
    mislabelled as nightly.
    """
    if not isinstance(qualifier, str):
        return "night"
    q = qualifier.strip().lower()
    if q == "night":
        return "night"
    if q in ("monthly", "month"):
        return "month"
    if q in ("week", "weekly"):
        return "week"
    # Any other value (e.g. 'for 7 nights', '3 nights') is treated as a
    # stay-period total to avoid mislabelling it as a nightly rate.
    return "stay"


def _parse_price_amount(val: Any) -> Decimal | None:
    """Parse a price value that may be a number or a formatted string like ``'$120'``.

    Strips common leading currency symbols (``$``, ``€``, ``£``, ``¥``, ``₹``)
    and internal commas before attempting a ``Decimal`` conversion.  Returns
    ``None`` on any parse failure so callers can fall through to the next
    candidate field.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        try:
            return Decimal(str(val))
        except Exception:
            return None
    if isinstance(val, str):
        cleaned = val.strip().lstrip("$€£¥₹").replace(",", "").strip()
        try:
            return Decimal(cleaned)
        except Exception:
            return None
    return None


def _build_actor_input(url: str, actor_id: str) -> dict[str, Any]:
    """Return the actor-specific Apify input payload for *url*.

    Different public Airbnb actors expect different input contracts:
    - ``tri_angle~airbnb-rooms-urls-scraper``: ``startUrls`` array with
      ``currency`` to request priced output (listing details, dated price,
      photos, host, amenities, rules).
    - ``curious_coder~airbnb-scraper``: ``urls`` array with scrape flags.
    - Generic fallback: ``startUrls`` array with ``maxListings=1``.
    """
    if actor_id in _TRI_ANGLE_ROOMS_ACTOR_IDS:
        payload: dict[str, Any] = {
            "startUrls": [{"url": url}],
            "currency": "USD",
        }
        # Dated price is only returned by the actor when checkIn/checkOut are
        # passed explicitly in the input; dated query params in the URL alone
        # are not enough for the tri_angle actor.
        try:
            qs = parse_qs(urlparse(url).query)
            check_in = (qs.get("check_in") or [None])[0]
            check_out = (qs.get("check_out") or [None])[0]
            if check_in:
                payload["checkIn"] = check_in
            if check_out:
                payload["checkOut"] = check_out
        except Exception:
            pass
        return payload

    if actor_id in _CURIOUS_CODER_ACTOR_IDS:
        return {
            "urls": [url],
            "currency": "USD",
            "scrapeAvailability": False,
            "scrapeDetail": False,
            "scrapeReviews": True,
        }

    return {"startUrls": [{"url": url}], "maxListings": 1}


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
    # Field lookup order (most-specific to least-specific):
    # 1. pricing.rate.amount  — curious_coder actor nested structure
    # 2. costPerNight         — curious_coder actor flat field
    # 3. price                — tri_angle actor field (object or scalar)
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
    if price is None and raw.get("costPerNight") is not None:
        try:
            price = PriceInfo(
                amount=Decimal(str(raw["costPerNight"])),
                currency=str(raw.get("currency") or "USD"),
                period="night",
            )
        except Exception:
            pass
    if price is None and raw.get("price") is not None:
        price_raw = raw["price"]
        # tri_angle actor returns price as an object; scalar (numeric/string)
        # values are also accepted for backward compatibility.
        if isinstance(price_raw, dict):
            # Derive the period from the qualifier so dated stays (weekly,
            # monthly, etc.) are not mislabelled as nightly.
            period = _period_from_qualifier(price_raw.get("qualifier"))
            # Amount priority for the tri_angle price object:
            # 1. discountedPrice — the actual discounted amount for the period;
            #    populated for both undated and dated requests.
            # 2. price (top-level display string) — non-empty for undated
            #    nightly requests; empty string when dates are given.
            # 3. basePrice.price — last resort (also represents the period
            #    total for dated requests, not a per-night rate).
            amount: Decimal | None = None
            amount = _parse_price_amount(price_raw.get("discountedPrice"))
            if amount is None:
                amount = _parse_price_amount(price_raw.get("price"))
            if amount is None:
                base_price = price_raw.get("basePrice")
                if isinstance(base_price, dict):
                    amount = _parse_price_amount(base_price.get("price"))
            if amount is not None:
                try:
                    price = PriceInfo(
                        amount=amount,
                        currency=str(raw.get("currency") or "USD"),
                        period=period,
                    )
                except Exception:
                    pass
        else:
            amount = _parse_price_amount(price_raw)
            if amount is not None:
                try:
                    price = PriceInfo(
                        amount=amount,
                        currency=str(raw.get("currency") or "USD"),
                        period="night",
                    )
                except Exception:
                    pass
    # Attach cleaning/service fees when present (tri_angle actor fields).
    # _parse_price_amount handles both numeric values and formatted strings
    # like '$25' so fees are not silently dropped when the actor returns strings.
    if price is not None:
        cleaning_fee_amount = _parse_price_amount(raw.get("cleaningFee"))
        if cleaning_fee_amount is not None:
            price = price.model_copy(update={"cleaning_fee": cleaning_fee_amount})
        service_fee_amount = _parse_price_amount(raw.get("serviceFee"))
        if service_fee_amount is not None:
            price = price.model_copy(update={"service_fee": service_fee_amount})

    # --- location ------------------------------------------------------------
    raw_location = raw.get("location")
    if not isinstance(raw_location, dict):
        raw_location = {}

    def _float_or_none(val: Any) -> float | None:
        try:
            return float(val) if val is not None else None
        except (TypeError, ValueError):
            return None

    # Use _first_non_none so that zero-valued coordinates (e.g. lat=0, lng=0)
    # are preserved rather than treated as falsy and silently dropped.
    location = ListingLocation(
        latitude=_float_or_none(
            _first_present(
                _first_non_none(raw, "lat", "latitude"),
                raw_location.get("latitude"),
            )
        ),
        longitude=_float_or_none(
            _first_present(
                _first_non_none(raw, "lng", "longitude"),
                raw_location.get("longitude"),
            )
        ),
        address=raw.get("address") or raw_location.get("address") or None,
        city=raw.get("city") or None,
        country=raw.get("country") or raw.get("countryCode") or None,
        neighbourhood=raw.get("neighbourhood") or raw_location.get("description") or None,
    )

    # --- amenities -----------------------------------------------------------
    raw_amenities = raw.get("amenities")
    amenities: list[str] = []
    if isinstance(raw_amenities, list):
        if raw_amenities and isinstance(raw_amenities[0], dict):
            amenities = [
                str(item.get("title"))
                for item in raw_amenities
                if isinstance(item, dict) and item.get("available") is not False and item.get("title")
            ]
        else:
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
    host_details = raw.get("hostDetails")
    if isinstance(host_details, dict):
        host_name = host_name or host_details.get("name") or None
        raw_superhost = host_details.get("isSuperhost")
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
            _first_non_none(raw, "personCapacity", "maxGuests", "maxGuestCapacity")
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

    async def fetch(self, url: str) -> AdapterResult:
        """Fetch the Airbnb listing at *url* via Apify and return an ``AdapterResult``.

        Parameters
        ----------
        url:
            A recognised Airbnb listing URL (see ``supports_url``).

        Returns
        -------
        AdapterResult
            Contains the unmodified Apify actor item (``raw``) and the
            normalised listing (``listing``).

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
            _build_actor_input(url, settings.apify_airbnb_actor_id)
        )
        if not items:
            raise ValueError(
                f"Apify returned an empty dataset for URL: {url!r}. "
                "The listing may not exist or scraping may have been blocked."
            )
        raw = items[0]
        return AdapterResult(raw=raw, listing=_normalize(url, raw))
