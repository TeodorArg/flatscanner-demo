# Plan 031: Simple Amenities Block

## Approach

The implementation requires no new modules or pipeline stages. Amenities are
already scraped by the Airbnb adapter and stored on `NormalizedListing`. The
work is entirely in threading the data through to the formatter and adding
display logic.

## Steps

1. **`AnalysisResult.amenities`** — Add `amenities: list[str]` field with an
   empty-list default.
2. **Job processor** — In `process_job()`, copy `listing.amenities` into the
   assembled `AnalysisResult` via `model_copy`.
3. **i18n catalog** — Add `"fmt.amenities_label"` entries for RU, EN, ES.
4. **Formatter** — Add `_format_amenities(result, language)` helper that
   renders up to 10 amenities as a bold label + comma-separated inline list.
   Hook it into `format_analysis_message()` between risks and reviews.
5. **Tests** — Focused tests in `test_telegram_formatter.py` covering
   presence, omission, 10-item cap, HTML escaping, and multilingual labels.

## Notes

- No translation pass needed: amenity labels come from the scraper in English
  and are rendered verbatim.
- The 10-item cap keeps messages concise; no ellipsis is added for the
  truncated items.
