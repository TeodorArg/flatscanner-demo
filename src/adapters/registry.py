"""Provider resolution registry.

Maps a listing URL to the appropriate ``ListingAdapter`` instance.
Downstream code (Telegram dispatcher, job workers, …) uses this module to
stay provider-agnostic: it never imports Airbnb-specific logic directly.

Usage
-----
    from src.adapters.registry import detect_provider, resolve_adapter

    adapter = resolve_adapter(url)          # ListingAdapter | None
    provider = detect_provider(url)         # ListingProvider (UNKNOWN if unsupported)
"""

from __future__ import annotations

from src.adapters.airbnb import AirbnbAdapter
from src.adapters.base import ListingAdapter
from src.domain.listing import ListingProvider

# Ordered list of registered adapters.  The first adapter whose
# ``supports_url`` returns True wins.  Add new adapters here as new
# listing providers are implemented.
_ADAPTERS: list[ListingAdapter] = [
    AirbnbAdapter(),
]


def resolve_adapter(url: str) -> ListingAdapter | None:
    """Return the first adapter that recognises *url*, or None.

    The result is suitable for direct use in the analysis pipeline once
    ``fetch`` is implemented on each adapter.
    """
    for adapter in _ADAPTERS:
        if adapter.supports_url(url):
            return adapter
    return None


def detect_provider(url: str) -> ListingProvider:
    """Return the ``ListingProvider`` for *url*, or ``ListingProvider.UNKNOWN``.

    Convenience wrapper around ``resolve_adapter`` for callers that only
    need the provider enum without a full adapter reference.
    """
    adapter = resolve_adapter(url)
    return adapter.provider if adapter is not None else ListingProvider.UNKNOWN
