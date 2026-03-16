"""Airbnb listing adapter.

Handles Airbnb URL recognition and (once the Apify back-end is wired up)
listing data retrieval and normalisation.

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
from urllib.parse import urlparse

from src.adapters.base import ListingAdapter
from src.domain.listing import ListingProvider, NormalizedListing

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
_AIRBNB_LISTING_PATH_RE = re.compile(r"^/rooms/[^/?#\s]+/?$", re.IGNORECASE)


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


class AirbnbAdapter(ListingAdapter):
    """Adapter for Airbnb listing URLs.

    ``fetch`` is intentionally unimplemented until the Apify extraction
    layer is wired up in a later task.
    """

    provider = ListingProvider.AIRBNB

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
        """Not yet implemented — Apify extraction is a later task."""
        raise NotImplementedError(
            "AirbnbAdapter.fetch is not yet implemented. "
            "Apify-backed extraction will be added in a subsequent task."
        )
