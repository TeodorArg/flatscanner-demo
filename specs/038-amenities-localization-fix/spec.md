# Spec: Amenities Localization Fix

## Problem

The compact amenities block in the Telegram formatter shows English-only text for any
Airbnb amenity label that does not have a matching entry in the i18n catalog.

Two root causes:

1. **Thin taxonomy** — `taxonomy.py` maps only ~30 Airbnb label strings to canonical keys.
   Dozens of common labels (iron, hair dryer, gym, hot tub, etc.) fall through to
   auto-slugified keys like `iron`, `hair_dryer`, and `gym` that have no catalog entry.

2. **Weak fallback** — `_label_amenity_key()` in `formatter.py` falls back to
   `key.replace("_", " ").capitalize()`, which only capitalizes the first letter of the
   whole string (e.g. "Hair dryer" instead of "Hair Dryer") and is always English.

## Goal

Display properly localized labels for as many amenities as possible, and ensure
that any remaining unknown labels are rendered in a readable form regardless of
the user's language.

## Scope

- Expand `taxonomy.py` `_LABEL_SPECS` to cover the most common Airbnb amenity strings
  including label variants (washer/dryer location suffixes, AC prefix variants, parking
  types, TV/streaming variants, Wi-Fi speed suffixes, etc.).
- Add `amenity.*` i18n entries in `catalog.py` for all new canonical keys introduced.
- Change the fallback in `_label_amenity_key()` from `.capitalize()` to `.title()` so
  multi-word unknown keys render consistently (e.g. "Hair Dryer" not "Hair dryer").
- Do NOT change the overall message layout or section structure.

## Out of scope

- Storing original provider labels in `AmenitiesInsightsBlock` (requires model change).
- Machine-translating unknown amenity labels at runtime.
- Adding a new i18n language.
