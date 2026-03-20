"""Analysis context passed to every analysis module.

``AnalysisContext`` bundles the normalized listing, optional enrichment outcome,
and a convenience ``provider`` property so modules do not need to reach into
the listing directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.domain.listing import ListingProvider, NormalizedListing

if TYPE_CHECKING:
    from src.domain.raw_payload import RawPayload
    from src.enrichment.runner import EnrichmentOutcome


@dataclass
class AnalysisContext:
    """Input context supplied to every analysis module run.

    Parameters
    ----------
    listing:
        Normalized, provider-agnostic listing data.
    enrichment:
        Optional enrichment outcome.  ``None`` means enrichment was skipped;
        an ``EnrichmentOutcome`` with all-failures is still passed through so
        modules can inspect what was attempted.
    raw_payload:
        Optional raw adapter payload captured before normalisation.  Present
        when the job processor persisted the payload; ``None`` otherwise.
        Modules may use it for provider-specific signal extraction.
    """

    listing: NormalizedListing
    enrichment: "EnrichmentOutcome | None" = field(default=None)
    raw_payload: "RawPayload | None" = field(default=None)

    @property
    def provider(self) -> ListingProvider:
        """Listing provider, forwarded from the listing for convenience."""
        return self.listing.provider
