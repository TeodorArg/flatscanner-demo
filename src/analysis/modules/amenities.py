"""Amenities evidence modules."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.analysis.amenities.normalizers.airbnb import AirbnbAmenityNormalizer
from src.analysis.amenities.normalizers.generic import GenericAmenityNormalizer
from src.analysis.amenities.taxonomy import is_critical_missing
from src.analysis.module import ModuleResult
from src.domain.amenity_corpus import AmenityCorpus, AmenityAvailability
from src.domain.listing import ListingProvider


@dataclass
class AmenitiesEvidenceResult(ModuleResult):
    """Structured amenity evidence extracted from one listing source."""

    corpus: AmenityCorpus
    available_keys: list[str] = field(default_factory=list)
    unavailable_keys: list[str] = field(default_factory=list)
    critical_missing_keys: list[str] = field(default_factory=list)
    categories_present: list[str] = field(default_factory=list)


def _build_result(module_name: str, corpus: AmenityCorpus) -> AmenitiesEvidenceResult:
    available_keys = sorted(
        {
            item.canonical_key
            for item in corpus.items
            if item.availability == AmenityAvailability.AVAILABLE
        }
    )
    unavailable_keys = sorted(
        {
            item.canonical_key
            for item in corpus.items
            if item.availability == AmenityAvailability.UNAVAILABLE
        }
    )
    critical_missing_keys = sorted(
        {
            item.canonical_key
            for item in corpus.items
            if is_critical_missing(item.canonical_key, item.availability)
        }
    )
    categories_present = sorted(
        {
            item.category
            for item in corpus.items
            if item.availability == AmenityAvailability.AVAILABLE and item.category
        }
    )
    return AmenitiesEvidenceResult(
        module_name=module_name,
        corpus=corpus,
        available_keys=available_keys,
        unavailable_keys=unavailable_keys,
        critical_missing_keys=critical_missing_keys,
        categories_present=categories_present,
    )


class AirbnbAmenitiesEvidenceModule:
    """Provider-specific amenities evidence module for Airbnb listings."""

    name = "amenities_evidence"
    supported_providers: frozenset[ListingProvider] = frozenset({ListingProvider.AIRBNB})

    def __init__(self) -> None:
        self._normalizer = AirbnbAmenityNormalizer()
        self._generic_normalizer = GenericAmenityNormalizer()

    async def run(self, ctx) -> AmenitiesEvidenceResult:
        extraction = (
            self._normalizer.normalize(ctx.raw_payload.payload, ctx.listing)
            if ctx.raw_payload is not None
            else self._generic_normalizer.normalize({}, ctx.listing)
        )
        return _build_result(self.name, extraction.corpus)


class GenericAmenitiesEvidenceModule:
    """Generic fallback amenities evidence module."""

    name = "amenities_evidence"
    supported_providers: frozenset[ListingProvider] = frozenset()

    def __init__(self) -> None:
        self._normalizer = GenericAmenityNormalizer()

    async def run(self, ctx) -> AmenitiesEvidenceResult:
        extraction = self._normalizer.normalize({}, ctx.listing)
        return _build_result(self.name, extraction.corpus)
