# Tasks: Amenities Localization Fix

- [x] Write spec, plan, and tasks
- [x] Expand taxonomy in `src/analysis/amenities/taxonomy.py`
- [x] Add new `amenity.*` i18n entries in `src/i18n/catalog.py`
- [x] Improve `_label_amenity_key` fallback in `src/telegram/formatter.py`
- [x] Add `tests/test_amenities_localization.py`
- [x] Run tests and verify green (95 new tests pass; 2 pre-existing Apify-credential failures unaffected)
- [x] Commit and publish PR — https://github.com/alexgoodman53/flatscanner/pull/49
- [x] Follow-up: add `_boundary_match()` word-bounded substring fallback in taxonomy.py and "ac" alias so compound Airbnb labels ("32 inch HDTV", "AC split type ductless system", "Shared gym in building", "Coffee maker: pour over coffee") resolve to correct canonical keys and render localized in RU — 106 tests green
