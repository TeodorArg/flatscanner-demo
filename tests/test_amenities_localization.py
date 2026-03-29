"""Tests for amenities localization: taxonomy expansion and formatter fallback.

Covers:
- New taxonomy label mappings (exact and variant labels)
- New i18n catalog entries for all three languages
- Formatter _label_amenity_key fallback uses title-case for unknown keys
- Formatter renders new localized keys in RU, EN, ES
"""

from __future__ import annotations

import pytest

from src.analysis.amenities.taxonomy import canonicalize_amenity
from src.i18n.catalog import get_string
from src.i18n.types import Language
from src.telegram.formatter import _label_amenity_key


# ---------------------------------------------------------------------------
# Taxonomy: new label → canonical key mappings
# ---------------------------------------------------------------------------


class TestTaxonomyExpansion:
    @pytest.mark.parametrize(
        "label,expected_key",
        [
            # Wi-Fi variants
            ("Wifi – fast (100+ Mbps)", "wifi"),
            ("Wi-Fi – medium (25+ Mbps)", "wifi"),
            ("wi-fi – slow (< 25 mbps)", "wifi"),
            # Laundry location suffixes
            ("Free washer – In unit", "washer"),
            ("Free washer - In unit", "washer"),
            ("Free dryer – In building", "dryer"),
            ("Free dryer – In unit", "dryer"),
            # Kitchen
            ("Coffee maker", "coffee_maker"),
            ("Coffee", "coffee_maker"),
            ("Dining table", "dining_table"),
            ("Stove", "stove"),
            ("Oven", "oven"),
            ("Dishwasher", "dishwasher"),
            ("Wine glasses", "wine_glasses"),
            # Laundry
            ("Clothes drying rack", "clothes_drying_rack"),
            # Climate
            ("Central air conditioning", "air_conditioning"),
            ("Portable air conditioning", "air_conditioning"),
            ("Ceiling fan", "ceiling_fan"),
            ("Indoor fireplace", "indoor_fireplace"),
            ("Indoor fireplaces", "indoor_fireplace"),
            # Bathroom
            ("Hair dryer", "hair_dryer"),
            ("Towels", "towels"),
            ("Body soap", "body_soap"),
            ("Conditioner", "conditioner"),
            ("Shower gel", "shower_gel"),
            ("Cleaning products", "cleaning_products"),
            # Bedroom
            ("Iron", "iron"),
            ("Safe", "safe"),
            ("Extra pillows and blankets", "extra_pillows_blankets"),
            ("Room-darkening shades", "room_darkening_shades"),
            # Workspace
            ("Dedicated workspace", "dedicated_workspace"),
            ("Dedicated workspace – private room", "dedicated_workspace"),
            # Entertainment
            ("Cable TV", "tv"),
            ("HDTV", "tv"),
            ("Streaming services", "streaming_services"),
            # Internet
            ("Ethernet", "ethernet"),
            # Leisure
            ("Hot tub", "hot_tub"),
            ("Jacuzzi", "hot_tub"),
            ("Gym", "gym"),
            ("Sauna", "sauna"),
            # Access
            ("Private entrance", "private_entrance"),
            ("Self check-in", "self_checkin"),
            ("Lockbox", "self_checkin"),
            ("Keypad", "self_checkin"),
            ("Smart lock", "self_checkin"),
            # Parking
            ("Free parking on premises", "parking"),
            ("Free driveway parking on premises", "parking"),
            ("Paid parking off premises", "parking"),
            ("EV charger", "ev_charger"),
            # Outdoor
            ("Shared patio or balcony", "balcony"),
            ("Backyard", "balcony"),
            ("Outdoor shower", "outdoor_shower"),
            # Safety
            ("Fire extinguisher", "fire_extinguisher"),
            ("First aid kit", "first_aid_kit"),
        ],
    )
    def test_label_maps_to_canonical_key(self, label: str, expected_key: str) -> None:
        spec = canonicalize_amenity(label)
        assert spec.canonical_key == expected_key, (
            f"Label {label!r} → expected {expected_key!r}, got {spec.canonical_key!r}"
        )

    def test_unknown_label_slugified(self) -> None:
        spec = canonicalize_amenity("Some Exotic Feature")
        assert spec.canonical_key == "some_exotic_feature"

    def test_group_category_used_for_unknown_label(self) -> None:
        spec = canonicalize_amenity("Some Exotic Feature", group="Bathroom")
        assert spec.category == "bathroom"


# ---------------------------------------------------------------------------
# Regression: provider-compound Airbnb labels that failed before boundary match
# ---------------------------------------------------------------------------


class TestProviderCompoundLabels:
    """Labels reported in PR #49 follow-up: raw Airbnb strings that the
    exact-match dict did not cover.  They must now resolve to the correct
    canonical key via _boundary_match."""

    @pytest.mark.parametrize(
        "label,expected_key",
        [
            # TV with size prefix: "32 inch HDTV"
            ("32 inch HDTV", "tv"),
            # AC with model description: "AC - split type ductless system"
            ("AC - split type ductless system", "air_conditioning"),
            # Gym with location qualifier: "Shared gym in building"
            ("Shared gym in building", "gym"),
            # Coffee maker with preparation variant: "Coffee maker: pour over coffee"
            ("Coffee maker: pour over coffee", "coffee_maker"),
            # A few more patterns that follow the same compound structure
            ("65-inch HDTV", "tv"),
            ("AC - window unit", "air_conditioning"),
            ("Private gym in building", "gym"),
        ],
    )
    def test_compound_label_resolves(self, label: str, expected_key: str) -> None:
        spec = canonicalize_amenity(label)
        assert spec.canonical_key == expected_key, (
            f"Compound label {label!r} → expected {expected_key!r}, got {spec.canonical_key!r}"
        )

    def test_compound_tv_label_renders_localized_ru(self) -> None:
        from src.telegram.formatter import _label_amenity_key
        from src.analysis.amenities.taxonomy import canonicalize_amenity

        raw_label = "32 inch HDTV"
        spec = canonicalize_amenity(raw_label)
        ru_label = _label_amenity_key(spec.canonical_key, Language.RU)
        assert ru_label == "ТВ", f"Expected Russian 'ТВ', got {ru_label!r}"

    def test_compound_ac_label_renders_localized_ru(self) -> None:
        from src.telegram.formatter import _label_amenity_key
        from src.analysis.amenities.taxonomy import canonicalize_amenity

        raw_label = "AC - split type ductless system"
        spec = canonicalize_amenity(raw_label)
        ru_label = _label_amenity_key(spec.canonical_key, Language.RU)
        assert ru_label == "Кондиционер", f"Expected Russian 'Кондиционер', got {ru_label!r}"

    def test_compound_gym_label_renders_localized_ru(self) -> None:
        from src.telegram.formatter import _label_amenity_key
        from src.analysis.amenities.taxonomy import canonicalize_amenity

        raw_label = "Shared gym in building"
        spec = canonicalize_amenity(raw_label)
        ru_label = _label_amenity_key(spec.canonical_key, Language.RU)
        assert "Тренажёрный" in ru_label, f"Expected Russian gym label, got {ru_label!r}"

    def test_compound_coffee_label_renders_localized_ru(self) -> None:
        from src.telegram.formatter import _label_amenity_key
        from src.analysis.amenities.taxonomy import canonicalize_amenity

        raw_label = "Coffee maker: pour over coffee"
        spec = canonicalize_amenity(raw_label)
        ru_label = _label_amenity_key(spec.canonical_key, Language.RU)
        assert ru_label == "Кофемашина", f"Expected Russian 'Кофемашина', got {ru_label!r}"


# ---------------------------------------------------------------------------
# i18n catalog: new amenity entries exist for all languages
# ---------------------------------------------------------------------------


NEW_AMENITY_KEYS = [
    "dedicated_workspace",
    "iron",
    "hair_dryer",
    "safe",
    "extra_pillows_blankets",
    "room_darkening_shades",
    "towels",
    "body_soap",
    "conditioner",
    "shower_gel",
    "cleaning_products",
    "coffee_maker",
    "dining_table",
    "stove",
    "oven",
    "dishwasher",
    "wine_glasses",
    "clothes_drying_rack",
    "ceiling_fan",
    "indoor_fireplace",
    "hot_tub",
    "gym",
    "sauna",
    "streaming_services",
    "ethernet",
    "private_entrance",
    "self_checkin",
    "ev_charger",
    "outdoor_shower",
    "fire_extinguisher",
    "first_aid_kit",
]


class TestNewCatalogEntries:
    @pytest.mark.parametrize("key", NEW_AMENITY_KEYS)
    def test_entry_exists_for_all_languages(self, key: str) -> None:
        catalog_key = f"amenity.{key}"
        for lang in Language:
            value = get_string(catalog_key, lang)
            assert value, f"Empty string for {catalog_key!r} in {lang}"

    def test_russian_translations_are_non_english(self) -> None:
        # Spot-check that RU entries are not English placeholders.
        assert "Фен" in get_string("amenity.hair_dryer", Language.RU)
        assert "Тренажёрный" in get_string("amenity.gym", Language.RU)
        assert "Утюг" in get_string("amenity.iron", Language.RU)

    def test_spanish_translations_present(self) -> None:
        assert get_string("amenity.hot_tub", Language.ES) == "Jacuzzi"
        assert "Extintor" in get_string("amenity.fire_extinguisher", Language.ES)


# ---------------------------------------------------------------------------
# Formatter: _label_amenity_key
# ---------------------------------------------------------------------------


class TestLabelAmenityKeyFormatter:
    def test_known_key_returns_localized_en(self) -> None:
        assert _label_amenity_key("wifi", Language.EN) == "Wi-Fi"

    def test_known_key_returns_localized_ru(self) -> None:
        assert _label_amenity_key("gym", Language.RU) == "Тренажёрный зал"

    def test_known_key_returns_localized_es(self) -> None:
        assert _label_amenity_key("hot_tub", Language.ES) == "Jacuzzi"

    def test_unknown_key_falls_back_to_title_case(self) -> None:
        result = _label_amenity_key("some_exotic_feature", Language.RU)
        assert result == "Some Exotic Feature"

    def test_unknown_single_word_key_title_case(self) -> None:
        result = _label_amenity_key("espresso", Language.EN)
        assert result == "Espresso"

    def test_unknown_key_same_for_all_languages(self) -> None:
        key = "very_rare_amenity"
        results = {lang: _label_amenity_key(key, lang) for lang in Language}
        assert len(set(results.values())) == 1, "Fallback should be identical for all languages"
