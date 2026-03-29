# Spec 041: Full Amenities List Output

## Problem

Spec 031 introduced an amenities section but capped the output at 10 items and
rendered them as a comma-separated inline list. This limits visibility for
listings with many amenities and is inconsistent with the bullet-list style
used for strengths and risks.

## Solution

Remove the 10-item cap and change the amenities render to a bullet list (one
`- Item` per line), matching the formatting style already used for the strengths
and risks sections.

## Scope

- `_format_amenities()` in `src/telegram/formatter.py`: remove the 10-item cap;
  render all amenities as a bullet list.
- `tests/test_telegram_formatter.py`: replace `test_amenities_capped_at_ten`
  with `test_amenities_all_items_rendered`; update
  `test_amenities_present_when_non_empty` to assert bullet-list format.
- `tests/test_031_amenities_block.py`: update `test_amenities_capped_at_ten_items`
  and `test_amenities_comma_separated` to reflect the new behavior.

## Out of Scope

- Pagination or collapsing of long amenity lists.
- Any change to how amenities are scraped, translated, or stored.

## Acceptance Criteria

1. All amenities beyond 10 are rendered in the output (no cap).
2. Each amenity is rendered as `- <escaped item>` on its own line.
3. The section header and omission behavior are unchanged.
4. HTML escaping still applies to every amenity string.
5. Localized labels still work for RU, EN, and ES.
