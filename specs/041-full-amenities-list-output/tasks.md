# Tasks — 041 Full Amenities List Output

## Status: done

## Tasks

- [x] Update `src/telegram/formatter.py`: change `_format_amenities` to render all amenities as a bullet list (one item per line) instead of a comma-separated 10-item preview.
- [x] Update `tests/test_telegram_formatter.py`: replace `test_amenities_capped_at_ten` with `test_amenities_all_items_rendered` that asserts all items beyond 10 are present; update `test_amenities_present_when_non_empty` to assert bullet-list format (`- WiFi`).
- [x] Run formatter test subset and confirm green.
- [x] Create `specs/041-full-amenities-list-output/spec.md` and `plan.md` for PR Guard feature memory.
- [x] Update `tests/test_031_amenities_block.py`: replace `test_amenities_capped_at_ten_items` with `test_amenities_all_items_rendered`; replace `test_amenities_comma_separated` with `test_amenities_bullet_list_format`.
- [x] Re-run `tests/test_031_amenities_block.py` and `tests/test_telegram_formatter.py` — 44/44 passed.
- [x] Fix AI-review blocker (PR #52): update `format_analysis_message` to separate head/tail assembly and budget the amenities block so tail sections (reviews, stay price, price verdict) are always preserved; add `- [+N more]` overflow note in `_format_amenities` when truncating; add regression tests `test_long_amenities_does_not_truncate_price_verdict`, `test_long_amenities_adds_overflow_note`, and `test_long_amenities_preserves_price_verdict`; update spec/plan to document the real requirement. Re-ran 47/47 tests — all passed.
- [x] Fix tight-budget silent drop (AI review follow-up): update `_format_amenities` to return a compact `header + "- [+N more]"` section when the budget is positive but no individual bullet fits; add regression test `test_tight_budget_shows_compact_overflow_not_empty` testing `_format_amenities` directly at a calibrated budget; update `plan.md` to document the compact overflow fallback. Re-ran 48/48 tests — all passed.
- [x] Fix localization blocker (AI review follow-up): add `fmt.amenities_overflow` catalog key with RU/EN/ES translations; update `_format_amenities` to use `get_string` for all overflow marker strings instead of hardcoded English; add `test_overflow_marker_localized_russian` and `test_overflow_marker_localized_spanish` regression tests. Re-ran 51/51 tests — all passed.
