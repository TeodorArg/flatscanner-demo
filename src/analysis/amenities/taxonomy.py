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
    # --- Internet ---
    "wifi": AmenitySpec("wifi", "internet"),
    "wi-fi": AmenitySpec("wifi", "internet"),
    # Wi-Fi speed variants Airbnb appends after an en-dash (normalized to plain hyphen)
    "wifi - fast (100+ mbps)": AmenitySpec("wifi", "internet"),
    "wifi - medium (25+ mbps)": AmenitySpec("wifi", "internet"),
    "wifi - slow (< 25 mbps)": AmenitySpec("wifi", "internet"),
    "wi-fi - fast (100+ mbps)": AmenitySpec("wifi", "internet"),
    "wi-fi - medium (25+ mbps)": AmenitySpec("wifi", "internet"),
    "wi-fi - slow (< 25 mbps)": AmenitySpec("wifi", "internet"),
    "ethernet": AmenitySpec("ethernet", "internet"),
    # --- Kitchen ---
    "kitchen": AmenitySpec("kitchen", "kitchen"),
    "refrigerator": AmenitySpec("refrigerator", "kitchen"),
    "microwave": AmenitySpec("microwave", "kitchen"),
    "cooking basics": AmenitySpec("cooking_basics", "kitchen"),
    "dishes and silverware": AmenitySpec("dishes_and_silverware", "kitchen"),
    "hot water kettle": AmenitySpec("kettle", "kitchen"),
    "toaster": AmenitySpec("toaster", "kitchen"),
    "coffee maker": AmenitySpec("coffee_maker", "kitchen"),
    "coffee": AmenitySpec("coffee_maker", "kitchen"),
    "dining table": AmenitySpec("dining_table", "kitchen"),
    "stove": AmenitySpec("stove", "kitchen"),
    "oven": AmenitySpec("oven", "kitchen"),
    "dishwasher": AmenitySpec("dishwasher", "kitchen"),
    "wine glasses": AmenitySpec("wine_glasses", "kitchen"),
    # --- Laundry ---
    "washer": AmenitySpec("washer", "laundry"),
    "dryer": AmenitySpec("dryer", "laundry"),
    "free washer in building": AmenitySpec("washer", "laundry"),
    "free washer – in building": AmenitySpec("washer", "laundry"),
    "free washer - in building": AmenitySpec("washer", "laundry"),
    "free washer – in unit": AmenitySpec("washer", "laundry"),
    "free washer - in unit": AmenitySpec("washer", "laundry"),
    "free washer in unit": AmenitySpec("washer", "laundry"),
    "free dryer in building": AmenitySpec("dryer", "laundry"),
    "free dryer – in building": AmenitySpec("dryer", "laundry"),
    "free dryer - in building": AmenitySpec("dryer", "laundry"),
    "free dryer – in unit": AmenitySpec("dryer", "laundry"),
    "free dryer - in unit": AmenitySpec("dryer", "laundry"),
    "free dryer in unit": AmenitySpec("dryer", "laundry"),
    "clothes drying rack": AmenitySpec("clothes_drying_rack", "laundry"),
    # --- Climate ---
    "ac": AmenitySpec("air_conditioning", "climate"),
    "air conditioning": AmenitySpec("air_conditioning", "climate"),
    "central air conditioning": AmenitySpec("air_conditioning", "climate"),
    "portable air conditioning": AmenitySpec("air_conditioning", "climate"),
    "heating": AmenitySpec("heating", "climate"),
    "ceiling fan": AmenitySpec("ceiling_fan", "climate"),
    "indoor fireplace": AmenitySpec("indoor_fireplace", "climate"),
    "indoor fireplaces": AmenitySpec("indoor_fireplace", "climate"),
    # --- Bathroom ---
    "bathtub": AmenitySpec("bathtub", "bathroom"),
    "shampoo": AmenitySpec("shampoo", "bathroom"),
    "bidet": AmenitySpec("bidet", "bathroom"),
    "hot water": AmenitySpec("hot_water", "bathroom"),
    "hair dryer": AmenitySpec("hair_dryer", "bathroom"),
    "towels": AmenitySpec("towels", "bathroom"),
    "body soap": AmenitySpec("body_soap", "bathroom"),
    "conditioner": AmenitySpec("conditioner", "bathroom"),
    "shower gel": AmenitySpec("shower_gel", "bathroom"),
    "cleaning products": AmenitySpec("cleaning_products", "bathroom"),
    # --- Bedroom ---
    "hangers": AmenitySpec("hangers", "bedroom"),
    "bed linens": AmenitySpec("bed_linens", "bedroom"),
    "iron": AmenitySpec("iron", "bedroom"),
    "safe": AmenitySpec("safe", "bedroom"),
    "extra pillows and blankets": AmenitySpec("extra_pillows_blankets", "bedroom"),
    "room-darkening shades": AmenitySpec("room_darkening_shades", "bedroom"),
    # --- Workspace ---
    "dedicated workspace": AmenitySpec("dedicated_workspace", "office"),
    "dedicated workspace - private room": AmenitySpec("dedicated_workspace", "office"),
    # --- Entertainment ---
    "tv": AmenitySpec("tv", "entertainment"),
    "cable tv": AmenitySpec("tv", "entertainment"),
    "hdtv": AmenitySpec("tv", "entertainment"),
    "streaming services": AmenitySpec("streaming_services", "entertainment"),
    # --- Leisure ---
    "pool": AmenitySpec("pool", "leisure"),
    "hot tub": AmenitySpec("hot_tub", "leisure"),
    "jacuzzi": AmenitySpec("hot_tub", "leisure"),
    "gym": AmenitySpec("gym", "leisure"),
    "sauna": AmenitySpec("sauna", "leisure"),
    # --- Access ---
    "private entrance": AmenitySpec("private_entrance", "access"),
    "self check-in": AmenitySpec("self_checkin", "access"),
    "lockbox": AmenitySpec("self_checkin", "access"),
    "keypad": AmenitySpec("self_checkin", "access"),
    "smart lock": AmenitySpec("self_checkin", "access"),
    # --- Parking ---
    "free street parking": AmenitySpec("parking", "parking"),
    "free parking on premises": AmenitySpec("parking", "parking"),
    "free driveway parking on premises": AmenitySpec("parking", "parking"),
    "paid parking off premises": AmenitySpec("parking", "parking"),
    "paid parking on premises": AmenitySpec("parking", "parking"),
    "ev charger": AmenitySpec("ev_charger", "parking"),
    # --- Outdoor ---
    "private patio or balcony": AmenitySpec("balcony", "outdoor"),
    "shared patio or balcony": AmenitySpec("balcony", "outdoor"),
    "backyard": AmenitySpec("balcony", "outdoor"),
    "shared backyard - fully fenced": AmenitySpec("balcony", "outdoor"),
    "outdoor dining area": AmenitySpec("outdoor_dining", "outdoor"),
    "bbq grill": AmenitySpec("bbq_grill", "outdoor"),
    "outdoor shower": AmenitySpec("outdoor_shower", "outdoor"),
    # --- Essentials ---
    "essentials": AmenitySpec("essentials", "essentials"),
    # --- Safety ---
    "smoke alarm": AmenitySpec("smoke_alarm", "safety"),
    "carbon monoxide alarm": AmenitySpec("carbon_monoxide_alarm", "safety"),
    "fire extinguisher": AmenitySpec("fire_extinguisher", "safety"),
    "first aid kit": AmenitySpec("first_aid_kit", "safety"),
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


# Keys sorted longest-first so more-specific matches beat shorter aliases.
_LABEL_SPECS_BY_LENGTH: list[tuple[str, AmenitySpec]] = sorted(
    _LABEL_SPECS.items(), key=lambda kv: len(kv[0]), reverse=True
)


def _boundary_match(normalized: str) -> AmenitySpec | None:
    """Return the best spec by word-bounded substring search, longest key first.

    A key matches when it appears inside *normalized* at a word boundary:
    the character before the match must be non-alphanumeric (or start-of-string),
    and the character after the match must be non-alphanumeric (or end-of-string).
    This tolerates provider detail suffixes such as "Coffee maker: pour over coffee"
    or dimension prefixes such as "32 inch HDTV".
    """
    for key, spec in _LABEL_SPECS_BY_LENGTH:
        idx = normalized.find(key)
        if idx == -1:
            continue
        before_ok = idx == 0 or not normalized[idx - 1].isalnum()
        after_idx = idx + len(key)
        after_ok = after_idx == len(normalized) or not normalized[after_idx].isalnum()
        if before_ok and after_ok:
            return spec
    return None


def canonicalize_amenity(label: str, group: str | None = None) -> AmenitySpec:
    """Return canonical amenity mapping for a provider-specific label."""
    normalized = _normalize_label(label)
    spec = _LABEL_SPECS.get(normalized)
    if spec is not None:
        return spec
    spec = _boundary_match(normalized)
    if spec is not None:
        return spec
    return AmenitySpec(canonical_key=_slugify(label), category=_category_from_group(group))


def is_critical_missing(key: str, availability: AmenityAvailability) -> bool:
    """Return True when *key* is a critical missing amenity."""
    return availability == AmenityAvailability.UNAVAILABLE and key in CRITICAL_MISSING_KEYS
