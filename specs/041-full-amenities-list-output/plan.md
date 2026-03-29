# Plan 041: Full Amenities List Output

## Approach

The formatter change removes the 10-item slice cap and switches the render
from a comma-joined preview to a per-line bullet list.  A head/tail budget
ensures tail sections (reviews, stay price, price verdict) always survive even
when the amenities list is very long.

## Steps

1. **Formatter** — In `_format_amenities()` in `src/telegram/formatter.py`,
   remove the `[:10]` cap and change the render to a bullet list matching the
   strengths/risks pattern.
2. **Head/tail budgeting** — `format_analysis_message` assembles tail sections
   first, measures the remaining budget, then passes it to `_format_amenities`.
   This ensures tail sections are never displaced by a long amenities block.
3. **Overflow handling** — When the full list exceeds the budget,
   `_format_amenities` fits as many bullets as possible and appends a
   `- [+N more]` overflow note.  When the budget is so tight that no individual
   bullet fits but the header + compact overflow note still fits, the function
   returns that compact form rather than silently dropping the section.  The
   section is omitted only when the source amenities list is empty or when even
   the compact form exceeds the available budget.
4. **Formatter tests** — In `tests/test_telegram_formatter.py`, replace
   `test_amenities_capped_at_ten` with `test_amenities_all_items_rendered` and
   update `test_amenities_present_when_non_empty` to assert `- WiFi` style.
   Add regression tests for long-list budget preservation, overflow note, and
   the tight-budget compact-overflow edge case.
5. **031 block tests** — In `tests/test_031_amenities_block.py`, update
   `test_amenities_capped_at_ten_items` to assert items beyond 10 are present,
   and update `test_amenities_comma_separated` to assert bullet-list format.

## Notes

- No changes to models, pipeline, i18n catalog, or other modules.
- Spec 031 acceptance criterion 3 (10-item cap) is superseded by this spec.
- The budget approach (head/tail split) avoids the previous bug where unbounded
  amenities caused `_guard_length` to cut the price verdict from the tail.
- The compact overflow fallback prevents a non-empty amenities list from
  disappearing silently when the reserved budget is very tight.
