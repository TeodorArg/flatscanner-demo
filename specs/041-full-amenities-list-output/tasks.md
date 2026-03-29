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
