# Tasks — 041 Full Amenities List Output

## Status: done

## Tasks

- [x] Update `src/telegram/formatter.py`: change `_format_amenities` to render all amenities as a bullet list (one item per line) instead of a comma-separated 10-item preview.
- [x] Update `tests/test_telegram_formatter.py`: replace `test_amenities_capped_at_ten` with `test_amenities_all_items_rendered` that asserts all items beyond 10 are present; update `test_amenities_present_when_non_empty` to assert bullet-list format (`- WiFi`).
- [x] Run formatter test subset and confirm green.
