"""Generic review extractor.

``GenericReviewExtractor`` is the fallback extractor used when no
provider-specific extractor is available, or when the raw payload is absent.
It builds a ``ReviewsData`` from listing-level metadata only
(``rating`` and ``review_count``), producing no individual ``Review``
objects since there is no review text to extract.
"""

from __future__ import annotations

from typing import Any

from src.domain.review import ReviewsData


class GenericReviewExtractor:
    """Builds ``ReviewsData`` from listing-level metadata.

    This extractor never calls any external API — it simply reads the
    ``rating`` and ``review_count`` fields already present on the
    ``NormalizedListing``.  The ``reviews`` list is always empty because
    there is no source of individual review text without a raw payload.
    """

    def extract(
        self,
        payload: dict[str, Any],
        listing: Any,  # NormalizedListing — kept as Any to avoid circular import
    ) -> ReviewsData:
        """Produce a ``ReviewsData`` from listing-level metadata.

        Parameters
        ----------
        payload:
            Ignored; included for protocol compatibility.
        listing:
            Normalized listing supplying ``review_count`` and ``rating``.

        Returns
        -------
        ReviewsData
            ``reviews`` is always empty; ``total_count`` and
            ``average_rating`` are sourced from the listing when present.
        """
        total_count = 0
        if listing is not None and getattr(listing, "review_count", None) is not None:
            try:
                total_count = int(listing.review_count)
            except (TypeError, ValueError):
                total_count = 0

        average_rating: float | None = None
        if listing is not None:
            raw_rating = getattr(listing, "rating", None)
            if raw_rating is not None:
                try:
                    average_rating = float(raw_rating)
                except (TypeError, ValueError):
                    average_rating = None

        return ReviewsData(
            reviews=[],
            total_count=total_count,
            average_rating=average_rating,
        )
