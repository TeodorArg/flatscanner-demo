"""Generic review normalizer (fallback).

``GenericReviewNormalizer`` is the fallback normalizer used when no
provider-specific normalizer is available or when the raw payload is absent.
It builds a ``ReviewCorpus`` from listing-level metadata only (``rating`` and
``review_count``), producing no individual ``UnifiedReviewComment`` objects
since there is no source of individual review text without a raw payload.
"""

from __future__ import annotations

from typing import Any

from src.domain.review_corpus import ReviewCorpus, ReviewExtractionResult


class GenericReviewNormalizer:
    """Builds a ``ReviewCorpus`` from listing-level metadata.

    This normalizer never calls any external API — it simply reads the
    ``rating`` and ``review_count`` fields already present on the
    ``NormalizedListing``.  The ``comments`` list is always empty because
    there is no source of individual review text without a raw payload.
    """

    def normalize(
        self,
        payload: dict[str, Any],
        listing: Any,  # NormalizedListing — kept as Any to avoid circular import
    ) -> ReviewExtractionResult:
        """Produce a ``ReviewExtractionResult`` from listing-level metadata.

        Parameters
        ----------
        payload:
            Ignored; included so callers may use a uniform ``normalize``
            signature across all normalizer implementations.
        listing:
            Normalized listing supplying ``review_count``, ``rating``,
            ``provider``, ``source_id``, and ``source_url``.

        Returns
        -------
        ReviewExtractionResult
            ``corpus.comments`` is always empty; ``total_review_count`` and
            ``average_rating`` are sourced from the listing when present.
        """
        total_count: int | None = None
        if listing is not None and getattr(listing, "review_count", None) is not None:
            try:
                total_count = int(listing.review_count)
            except (TypeError, ValueError):
                total_count = None

        average_rating: float | None = None
        if listing is not None:
            raw_rating = getattr(listing, "rating", None)
            if raw_rating is not None:
                try:
                    average_rating = float(raw_rating)
                except (TypeError, ValueError):
                    average_rating = None

        provider = "unknown"
        if listing is not None:
            prov = getattr(listing, "provider", None)
            if prov is not None:
                provider = prov.value if hasattr(prov, "value") else str(prov)

        source_id = getattr(listing, "source_id", None) if listing is not None else None
        source_url = getattr(listing, "source_url", None) if listing is not None else None

        corpus = ReviewCorpus(
            source_provider=provider,
            source_listing_id=str(source_id) if source_id is not None else None,
            source_url=source_url,
            total_review_count=total_count,
            average_rating=average_rating,
            comments=[],
        )
        return ReviewExtractionResult(
            corpus=corpus,
            extracted_comment_count=0,
        )
