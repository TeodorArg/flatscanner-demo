"""Airbnb amenity normalizer."""

from __future__ import annotations

from typing import Any

from src.analysis.amenities.taxonomy import canonicalize_amenity
from src.domain.amenity_corpus import (
    AmenityAvailability,
    AmenityCorpus,
    AmenityExtractionResult,
    UnifiedAmenityItem,
)


def _str_or_none(val: Any) -> str | None:
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


def _availability_from_value(value: dict[str, Any], group_title: str | None) -> AmenityAvailability:
    raw = value.get("available")
    if raw is True:
        return AmenityAvailability.AVAILABLE
    if raw is False:
        return AmenityAvailability.UNAVAILABLE
    if isinstance(group_title, str) and group_title.strip().lower() == "not included":
        return AmenityAvailability.UNAVAILABLE
    return AmenityAvailability.UNKNOWN


class AirbnbAmenityNormalizer:
    """Normalize Airbnb amenities into a unified corpus."""

    def normalize(
        self,
        payload: dict[str, Any],
        listing: Any,  # NormalizedListing kept as Any to avoid circular import
    ) -> AmenityExtractionResult:
        raw_amenities = payload.get("amenities")
        items: list[UnifiedAmenityItem] = []
        dropped = 0

        if isinstance(raw_amenities, list):
            for group in raw_amenities:
                if isinstance(group, dict):
                    group_title = _str_or_none(group.get("title"))
                    raw_values = group.get("values")
                    if isinstance(raw_values, list):
                        for raw_value in raw_values:
                            if not isinstance(raw_value, dict):
                                dropped += 1
                                continue
                            label = _str_or_none(raw_value.get("title"))
                            if not label:
                                dropped += 1
                                continue
                            spec = canonicalize_amenity(label, group_title)
                            items.append(
                                UnifiedAmenityItem(
                                    source_provider="airbnb",
                                    canonical_key=spec.canonical_key,
                                    label=label,
                                    category=spec.category,
                                    availability=_availability_from_value(raw_value, group_title),
                                    source_group=group_title,
                                    subtitle=_str_or_none(raw_value.get("subtitle")),
                                )
                            )
                    else:
                        # Flat fallback shape: treat top-level title as an available amenity.
                        label = group_title
                        if label:
                            spec = canonicalize_amenity(label, group_title)
                            items.append(
                                UnifiedAmenityItem(
                                    source_provider="airbnb",
                                    canonical_key=spec.canonical_key,
                                    label=label,
                                    category=spec.category,
                                    availability=AmenityAvailability.AVAILABLE,
                                    source_group=group_title,
                                )
                            )
                        else:
                            dropped += 1
                elif isinstance(group, str) and group.strip():
                    spec = canonicalize_amenity(group)
                    items.append(
                        UnifiedAmenityItem(
                            source_provider="airbnb",
                            canonical_key=spec.canonical_key,
                            label=group.strip(),
                            category=spec.category,
                            availability=AmenityAvailability.AVAILABLE,
                        )
                    )
                else:
                    dropped += 1

        source_id = getattr(listing, "source_id", None) if listing is not None else None
        source_url = getattr(listing, "source_url", None) if listing is not None else None

        corpus = AmenityCorpus(
            source_provider="airbnb",
            source_listing_id=str(source_id) if source_id is not None else None,
            source_url=source_url,
            items=items,
        )
        return AmenityExtractionResult(
            corpus=corpus,
            extracted_item_count=len(items),
            dropped_item_count=dropped,
        )
