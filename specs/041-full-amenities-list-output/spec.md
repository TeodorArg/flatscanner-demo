# Spec 041: Full Amenities List Output

## Problem

Spec 031 introduced an amenities section but capped the output at 10 items and
rendered them as a comma-separated inline list. This limits visibility for
listings with many amenities and is inconsistent with the bullet-list style
used for strengths and risks.

A further issue: removing the cap without budgeting allows a very long amenities
list to fill Telegram's 4096-character message limit, which causes the global
`_guard_length` tail cut to drop the reviews, stay-price, and price-verdict
sections — the most important parts of the output.

## Solution

Render all amenities as a bullet list (`- Item` per line). Before assembling the
final message, calculate how much space the tail sections (reviews, stay price,
price verdict) require and budget the amenities block to the remaining chars.
When the full list exceeds the budget, render as many items as fit and append a
`- [+N more]` overflow note. The tail sections are always preserved.

## Scope

- `format_analysis_message()` in `src/telegram/formatter.py`: separate assembly
  into head/tail parts; compute amenities budget from available space after tail.
- `_format_amenities()` in `src/telegram/formatter.py`: accept optional `budget`
  parameter; truncate with overflow note when necessary.
- `tests/test_telegram_formatter.py`: add `test_long_amenities_does_not_truncate_price_verdict`
  and `test_long_amenities_adds_overflow_note` regression tests.
- `tests/test_031_amenities_block.py`: add `test_long_amenities_preserves_price_verdict`.

## Out of Scope

- Pagination or collapsing of long amenity lists beyond the overflow note.
- Any change to how amenities are scraped, translated, or stored.

## Acceptance Criteria

1. All amenities are rendered when the list fits within the available budget.
2. Each amenity is rendered as `- <escaped item>` on its own line.
3. The section header and omission behavior are unchanged.
4. HTML escaping still applies to every amenity string.
5. Localized labels still work for RU, EN, and ES.
6. When amenities exceed the budget, a `- [+N more]` overflow note appears.
7. The price verdict (and other tail sections) always appear in the final message
   regardless of how many amenities the listing has.
