# Plan 025 — Telegram Analysis Progress UX

## Affected files

| File | Change |
|---|---|
| `src/i18n/catalog.py` | Update `msg.analysing` (remove URL placeholder); add `msg.progress.fetching`, `msg.progress.analysing` |
| `src/domain/listing.py` | Add `telegram_progress_message_id: int \| None = None` to `AnalysisJob` |
| `src/telegram/sender.py` | Add `send_message_return_id`, `send_chat_action`, `delete_message` |
| `src/telegram/router.py` | Analyse path: send progress msg → get id → attach to job → enqueue → return early |
| `src/jobs/processor.py` | Import new sender helpers; add typing heartbeat; update progress at stages; delete progress before final send |
| `tests/test_telegram_routing.py` | Update analyse-path tests (mock `send_message_return_id`, assert no URL in progress msg) |
| `tests/test_progress_ux.py` | New focused tests for progress UX |

## Step sequence

1. i18n catalog changes (no dependencies).
2. Domain model change (`AnalysisJob` field).
3. Sender helpers (no dependencies).
4. Router refactor (depends on sender + domain model).
5. Processor refactor (depends on sender + domain model).
6. Update existing tests.
7. Add new tests.
8. Validate with `pytest`.
