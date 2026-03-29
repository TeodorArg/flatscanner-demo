"""Unified amenity corpus models.

Provider-agnostic models for normalized amenity data. These become the
canonical source contract for amenities evidence modules and later
comparison modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AmenityAvailability(str, Enum):
    """Availability state for one normalized amenity item."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class UnifiedAmenityItem:
    """A single normalized amenity item from any provider."""

    source_provider: str
    canonical_key: str
    label: str
    category: str
    availability: AmenityAvailability
    source_group: str | None = None
    subtitle: str | None = None


@dataclass
class AmenityCorpus:
    """Unified amenity corpus for a single listing."""

    source_provider: str
    source_listing_id: str | None = None
    source_url: str | None = None
    items: list[UnifiedAmenityItem] = field(default_factory=list)


@dataclass
class AmenityExtractionResult:
    """Result of an amenity normalization operation."""

    corpus: AmenityCorpus
    extracted_item_count: int
    dropped_item_count: int = 0
    warnings: list[str] = field(default_factory=list)
