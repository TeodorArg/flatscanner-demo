# Plan 028 - Airbnb Migration to Tri_angle Scrapers

## Migration strategy

Do not switch both concerns in one PR. Land the migration in two small slices.

## Slice 1 - Listing / Details / Price / Photos

### Goal

Replace `curious_coder~airbnb-scraper` with `tri_angle~airbnb-rooms-urls-scraper`
for the core Airbnb listing adapter path.

### Affected files

| File | Change |
|---|---|
| `src/app/config.py` | Change default Airbnb listing actor id to the `tri_angle` room-URL actor |
| `src/adapters/airbnb.py` | Update actor input contract and normalization for the new raw schema |
| `tests/test_airbnb_extraction.py` | Replace or extend fixtures for the new actor schema |
| `tests/test_analysis.py` | Adjust prompt/path expectations if pricing fields change |
| `docs/project/backend/backend-docs.md` | Record the listing actor split and new default listing actor |
| `specs/028-airbnb-triangle-scrapers-migration/tasks.md` | Track slice completion |

### Constraints

- Keep the existing adapter interface intact
- Keep current Telegram delivery behavior intact
- Do not implement dedicated photo analysis yet
- Preserve raw payload capture for future photo/replay work

## Slice 2 - Reviews Source Abstraction

### Goal

Move Airbnb review ingestion behind a dedicated source abstraction.

### Affected areas

| Area | Change |
|---|---|
| `src/app/config.py` | Add dedicated Airbnb review-source configuration |
| `src/analysis/reviews/` | Add a dedicated Airbnb review source fetch path |
| `src/analysis/modules/reviews.py` | Use the dedicated reviews source for Airbnb |
| `tests/test_reviews_module.py` | Cover dedicated reviews ingestion path |
| `tests/test_review_corpus_normalization.py` | Add or update fixtures for any flat per-review schema |
| `docs/project/backend/backend-docs.md` | Record the listing actor split and reviews abstraction |

## Order

1. Land Slice 1
2. Validate price/details path in production
3. Land Slice 2
4. Run a final end-to-end smoke with listing + reviews working together
