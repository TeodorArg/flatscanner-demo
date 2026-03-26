# Tasks 025 — Telegram Analysis Progress UX

## Status: done

- [x] Create spec, plan, tasks files
- [x] Update `src/i18n/catalog.py`
- [x] Add `telegram_progress_message_id` to `AnalysisJob`
- [x] Add sender helpers (`send_message_return_id`, `send_chat_action`, `delete_message`)
- [x] Refactor router analyse path
- [x] Add progress stages + heartbeat + delete to `processor.py`
- [x] Update `tests/test_telegram_routing.py`
- [x] Update `tests/test_chat_language.py` and `tests/test_jobs.py`
- [x] Add `tests/test_progress_ux.py`
- [x] All 950 tests pass

## Follow-up fixes (2026-03-26)

- [x] Expand progress stages to 4: `extracting` → `enriching` → `analysing` → `preparing`
  - Renamed `msg.progress.fetching` → `msg.progress.extracting` (new text)
  - Updated `msg.progress.analysing` text ("Analyzing reviews and listing details")
  - Added `msg.progress.enriching` ("Checking area and infrastructure")
  - Added `msg.progress.preparing` ("Preparing final report")
  - Processor updated: stage updates placed before fetch, before enrichments, before module runner, before translation
- [x] Fix enqueue failure cleanup in router: best-effort `delete_message` on `RedisError` after progress msg already sent
- [x] Tests updated: new catalog key tests, 4-stage ordering assertion, enqueue-failure cleanup test
