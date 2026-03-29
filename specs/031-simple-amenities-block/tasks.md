# Tasks 031: Simple Amenities Block

## Status: done

## Task List

- [x] Add `amenities: list[str]` field to `AnalysisResult`
- [x] Map `listing.amenities` -> `result.amenities` in job processor
- [x] Add `"fmt.amenities_label"` to i18n catalog (RU / EN / ES)
- [x] Implement `_format_amenities()` in `src/telegram/formatter.py`
- [x] Hook `_format_amenities()` into `format_analysis_message()`
- [x] Add focused tests in `tests/test_telegram_formatter.py`
- [x] Create `specs/031-simple-amenities-block/` folder with spec, plan, tasks
- [x] Commit changes on assigned branch

- [x] AI Review follow-up: remove amenities from LLM translation path; update TestAmenitiesTranslation tests

## Validation

- `python -m pytest tests/test_031_amenities_block.py tests/test_telegram_formatter.py tests/test_translation_service.py -q` - 73 passed
