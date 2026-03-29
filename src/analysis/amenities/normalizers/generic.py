"""Generic amenity normalizer fallback."""

from __future__ import annotations

from typing import Any

from src.analysis.amenities.taxonomy import canonicalize_amenity
from src.domain.amenity_corpus import (
    AmenityAvailability,
    AmenityCorpus,
    AmenityExtractionResult,
    UnifiedAmenityItem,
)


class GenericAmenityNormalizer:
    """Normalize fallback flat amenity labels from ``listing.amenities``."""

    def normalize(
        self,
        payload: dict[str, Any],
        listing: Any,  # NormalizedListing kept as Any to avoid circular import
    ) -> AmenityExtractionResult:
        source_provider = "unknown"
        source_id = None
        source_url = None
        labels: list[str] = []

        if listing is not None:
            prov = getattr(listing, "provider", None)
            if prov is not None:
                source_provider = prov.value if hasattr(prov, "value") else str(prov)
            source_id = getattr(listing, "source_id", None)
            source_url = getattr(listing, "source_url", None)
            raw_labels = getattr(listing, "amenities", [])
            if isinstance(raw_labels, list):
                labels = [str(label).strip() for label in raw_labels if str(label).strip()]

        items = []
        for label in labels:
            spec = canonicalize_amenity(label)
            items.append(
                UnifiedAmenityItem(
                    source_provider=source_provider,
                    canonical_key=spec.canonical_key,
                    label=label,
                    category=spec.category,
                    availability=AmenityAvailability.AVAILABLE,
                )
            )

        corpus = AmenityCorpus(
            source_provider=source_provider,
            source_listing_id=str(source_id) if source_id is not None else None,
            source_url=source_url,
            items=items,
        )
        return AmenityExtractionResult(corpus=corpus, extracted_item_count=len(items))
