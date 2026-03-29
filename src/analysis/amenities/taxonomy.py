"""Canonical amenity taxonomy and helpers."""

from __future__ import annotations

from dataclasses import dataclass
import re

from src.domain.amenity_corpus import AmenityAvailability


@dataclass(frozen=True)
class AmenitySpec:
    """Canonical amenity mapping result."""

    canonical_key: str
    category: str


_LABEL_SPECS: dict[str, AmenitySpec] = {
    "wifi": AmenitySpec("wifi", "internet"),
    "wi-fi": AmenitySpec("wifi", "internet"),
    "kitchen": AmenitySpec("kitchen", "kitchen"),
    "free street parking": AmenitySpec("parking", "parking"),
    "pool": AmenitySpec("pool", "leisure"),
    "tv": AmenitySpec("tv", "entertainment"),
    "free washer in building": AmenitySpec("washer", "laundry"),
    "free washer – in building": AmenitySpec("washer", "laundry"),
    "free washer - in building": AmenitySpec("washer", "laundry"),
    "washer": AmenitySpec("washer", "laundry"),
    "dryer": AmenitySpec("dryer", "laundry"),
    "air conditioning": AmenitySpec("air_conditioning", "climate"),
    "heating": AmenitySpec("heating", "climate"),
    "bathtub": AmenitySpec("bathtub", "bathroom"),
    "shampoo": AmenitySpec("shampoo", "bathroom"),
    "bidet": AmenitySpec("bidet", "bathroom"),
    "hot water": AmenitySpec("hot_water", "bathroom"),
    "hangers": AmenitySpec("hangers", "bedroom"),
    "bed linens": AmenitySpec("bed_linens", "bedroom"),
    "refrigerator": AmenitySpec("refrigerator", "kitchen"),
    "microwave": AmenitySpec("microwave", "kitchen"),
    "cooking basics": AmenitySpec("cooking_basics", "kitchen"),
    "dishes and silverware": AmenitySpec("dishes_and_silverware", "kitchen"),
    "hot water kettle": AmenitySpec("kettle", "kitchen"),
    "toaster": AmenitySpec("toaster", "kitchen"),
    "private patio or balcony": AmenitySpec("balcony", "outdoor"),
    "outdoor dining area": AmenitySpec("outdoor_dining", "outdoor"),
    "bbq grill": AmenitySpec("bbq_grill", "outdoor"),
    "essentials": AmenitySpec("essentials", "essentials"),
    "smoke alarm": AmenitySpec("smoke_alarm", "safety"),
    "carbon monoxide alarm": AmenitySpec("carbon_monoxide_alarm", "safety"),
}

_GROUP_CATEGORY_ALIASES: dict[str, str] = {
    "bathroom": "bathroom",
    "bedroom and laundry": "laundry",
    "entertainment": "entertainment",
    "heating and cooling": "climate",
    "internet and office": "internet",
    "kitchen and dining": "kitchen",
    "outdoor": "outdoor",
    "parking and facilities": "parking",
    "not included": "other",
}

CRITICAL_MISSING_KEYS: frozenset[str] = frozenset({
    "smoke_alarm",
    "carbon_monoxide_alarm",
    "heating",
    "essentials",
})


def _normalize_label(value: str) -> str:
    text = value.strip().lower()
    text = text.replace("—", "-").replace("–", "-")
    text = re.sub(r"\s+", " ", text)
    return text


def _slugify(value: str) -> str:
    text = _normalize_label(value)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "other"


def _category_from_group(group: str | None) -> str:
    if not group:
        return "other"
    normalized = _normalize_label(group)
    return _GROUP_CATEGORY_ALIASES.get(normalized, _slugify(group))


def canonicalize_amenity(label: str, group: str | None = None) -> AmenitySpec:
    """Return canonical amenity mapping for a provider-specific label."""
    normalized = _normalize_label(label)
    spec = _LABEL_SPECS.get(normalized)
    if spec is not None:
        return spec
    return AmenitySpec(canonical_key=_slugify(label), category=_category_from_group(group))


def is_critical_missing(key: str, availability: AmenityAvailability) -> bool:
    """Return True when *key* is a critical missing amenity."""
    return availability == AmenityAvailability.UNAVAILABLE and key in CRITICAL_MISSING_KEYS
