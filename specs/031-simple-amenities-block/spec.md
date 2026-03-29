# Spec 031: Simple Amenities Block

## Problem

Listings scraped from Airbnb include an `amenities` list. This data was
collected by the adapter but never surfaced in the Telegram output delivered
to the user, leaving a useful signal hidden.

## Solution

Carry the scraped `amenities` list from `NormalizedListing` through
`AnalysisResult` and render it as a compact section in the Telegram message
formatter.

## Scope

- `AnalysisResult.amenities: list[str]` — field to hold amenity labels.
- Job processor maps `listing.amenities` → `result.amenities`.
- `_format_amenities()` in `src/telegram/formatter.py` renders up to 10
  amenities as a bold-labelled comma-separated line.
- i18n catalog entry `"fmt.amenities_label"` for RU / EN / ES.
- Focused tests in `tests/test_telegram_formatter.py`.

## Out of Scope

- Amenity translation or normalization (labels are rendered as-is from the
  scraper).
- A dedicated analysis module — amenities need no AI interpretation at this
  stage.
- Filtering, deduplication, or taxonomy mapping of amenity strings.

## Acceptance Criteria

1. A non-empty `result.amenities` list renders a localized bold label
   followed by the items as a comma-separated inline list.
2. The section is omitted when `result.amenities` is empty.
3. At most 10 amenities appear (the list is truncated silently).
4. All amenity strings are HTML-escaped before output.
5. The label is correctly localized for RU, EN, and ES.
6. The amenities section appears before the price verdict section.
