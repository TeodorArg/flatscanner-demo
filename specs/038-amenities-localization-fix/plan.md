# Plan: Amenities Localization Fix

## Changes

### 1. `src/analysis/amenities/taxonomy.py`

Add new entries to `_LABEL_SPECS` for:

- **Workspace**: "dedicated workspace" and variants → `dedicated_workspace`
- **Bedroom**: "iron" → `iron`; "safe" → `safe`;
  "extra pillows and blankets" → `extra_pillows_blankets`;
  "room-darkening shades" → `room_darkening_shades`
- **Bathroom**: "hair dryer" → `hair_dryer`; "towels" → `towels`;
  "body soap" → `body_soap`; "conditioner" → `conditioner`
- **Kitchen**: "coffee maker" / "coffee" → `coffee_maker`;
  "dining table" → `dining_table`; "stove" → `stove`; "oven" → `oven`;
  "dishwasher" → `dishwasher`
- **Laundry**: washer/dryer location variants (in unit, in building) → `washer`/`dryer`;
  "clothes drying rack" → `clothes_drying_rack`
- **Climate**: "ceiling fan" → `ceiling_fan`; "indoor fireplace" → `indoor_fireplace`;
  "central air conditioning" / "portable air conditioning" → `air_conditioning`
- **Leisure**: "hot tub" / "jacuzzi" → `hot_tub`; "gym" → `gym`; "sauna" → `sauna`
- **Entertainment**: "cable tv" / "hdtv" → `tv`; "streaming services" → `streaming_services`
- **Internet**: "ethernet" → `ethernet`; Wi-Fi speed variants → `wifi`
- **Access**: "private entrance" → `private_entrance`; self-check-in variants → `self_checkin`
- **Parking**: "free parking on premises" variants → `parking`; "ev charger" → `ev_charger`
- **Outdoor**: "shared patio or balcony" / "backyard" → `balcony`;
  "outdoor shower" → `outdoor_shower`
- **Safety**: "fire extinguisher" → `fire_extinguisher`; "first aid kit" → `first_aid_kit`

### 2. `src/i18n/catalog.py`

Add `amenity.*` entries for every new canonical key that is NOT an alias of an
existing key:
`dedicated_workspace`, `iron`, `hair_dryer`, `safe`, `extra_pillows_blankets`,
`room_darkening_shades`, `towels`, `body_soap`, `conditioner`, `coffee_maker`,
`dining_table`, `stove`, `oven`, `dishwasher`, `clothes_drying_rack`, `ceiling_fan`,
`indoor_fireplace`, `hot_tub`, `gym`, `sauna`, `streaming_services`, `ethernet`,
`private_entrance`, `self_checkin`, `ev_charger`, `outdoor_shower`,
`fire_extinguisher`, `first_aid_kit`.

### 3. `src/telegram/formatter.py`

In `_label_amenity_key()`, change the fallback from `.capitalize()` to `.title()`.

### 4. Tests

Add `tests/test_amenities_localization.py` covering:
- Selected new taxonomy mappings (both exact and variant labels)
- New i18n catalog entries for all three languages
- Formatter fallback produces title-case output for unknown keys
- Formatter renders new localized keys correctly in RU, EN, ES
