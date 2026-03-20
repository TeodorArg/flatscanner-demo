"""Abstract base class for listing-source adapters.

Each adapter encapsulates source-platform-specific logic:
- URL recognition (``supports_url``)
- Raw data retrieval and normalization into ``NormalizedListing`` (``fetch``, to be
  implemented per-adapter once extraction back-ends are wired up)

Downstream pipeline code works against this interface so that adding a new
listing provider never requires changes outside ``src/adapters/``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

from src.domain.listing import ListingProvider, NormalizedListing


@dataclass
class AdapterResult:
    """Raw and normalised output from a single adapter fetch.

    ``raw`` is the unmodified provider response (e.g. the first item returned
    by the Apify actor).  It is captured to the raw payload store before any
    transformation so that normalisation can be replayed without re-fetching.

    ``listing`` is the normalised ``NormalizedListing`` produced from ``raw``.
    """

    raw: dict[str, Any]
    listing: NormalizedListing


class ListingAdapter(ABC):
    """Provider-agnostic contract for listing-source adapters.

    Subclasses must:
    - Set the ``provider`` class variable to the matching ``ListingProvider`` value.
    - Implement ``supports_url`` to recognise URLs handled by this adapter.
    - Implement ``fetch`` to retrieve and normalise listing data from the source.
    """

    provider: ClassVar[ListingProvider]

    @abstractmethod
    def supports_url(self, url: str) -> bool:
        """Return True if this adapter can handle *url*.

        Must be a pure, side-effect-free check — no network calls.
        """

    @abstractmethod
    async def fetch(self, url: str) -> AdapterResult:
        """Fetch the listing at *url* and return an ``AdapterResult``.

        The result carries both the unmodified provider response (``raw``) and
        the normalised ``NormalizedListing`` (``listing``).  The raw payload
        must be captured before any transformation.

        Raises ``NotImplementedError`` until the back-end extraction layer for
        this adapter is wired up.
        """
