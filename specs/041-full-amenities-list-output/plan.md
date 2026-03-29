# Plan 041: Full Amenities List Output

## Approach

The formatter change is a one-line removal (the slice cap) and a format-string
change (comma join → per-line bullet). The test updates mirror this exactly.

## Steps

1. **Formatter** — In `_format_amenities()` in `src/telegram/formatter.py`,
   remove the `[:10]` cap and change the render to a bullet list matching the
   strengths/risks pattern.
2. **Formatter tests** — In `tests/test_telegram_formatter.py`, replace
   `test_amenities_capped_at_ten` with `test_amenities_all_items_rendered` and
   update `test_amenities_present_when_non_empty` to assert `- WiFi` style.
3. **031 block tests** — In `tests/test_031_amenities_block.py`, update
   `test_amenities_capped_at_ten_items` to assert items beyond 10 are present,
   and update `test_amenities_comma_separated` to assert bullet-list format.

## Notes

- No changes to models, pipeline, i18n catalog, or other modules.
- Spec 031 acceptance criterion 3 (10-item cap) is superseded by this spec.
