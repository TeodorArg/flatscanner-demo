# Tasks: Multilingual Bot Output

## Spec

- [x] Define the canonical-English plus translated-output architecture
- [x] Capture the supported languages and default-language behavior
- [x] Record the language snapshot requirement for queued jobs
- [x] Record the approved decision: translated outputs are generated on demand and not persisted as cache artifacts

## Design

- [x] Define the `Language` enum and centralized i18n catalog structure
- [x] Define storage for Telegram chat language preference
- [x] Define how on-demand translation is invoked without creating a persisted translation cache layer
- [x] Decide the first translation model/provider for MVP multilingual output (same OpenRouter client/model as analysis)
- [x] Decide the UX for language switching in Telegram (`/language <code>` command-based)

## Implementation

- [x] Add `src/i18n/` with language types, catalog, and `get_string` helper
- [x] Add `src/storage/chat_preferences.py` — Redis-backed chat language preference repository
- [x] Extend `AnalysisJob` with `language` (defaults to `DEFAULT_LANGUAGE`)
- [x] Snapshot the effective language when enqueueing an analysis job
- [x] Localize immediate Telegram replies (`help`, `unsupported`, `analysing`) via i18n catalog
- [x] Keep `AnalysisService` canonical output in English for generated freeform blocks
- [x] Add `src/translation/` — on-demand translation service for structured freeform result blocks
- [x] Keep translated output ephemeral; do not persist it as a multilingual cache artifact
- [x] Update the formatter to render localized labels and consume translated blocks (`language` parameter + i18n catalog)
- [x] Add language switching flow in Telegram (`/language ru|en|es` command in dispatcher + router)
- [x] Add formatter i18n catalog keys (section labels, verdict labels, truncation suffix)

## Validation

- [x] Add tests for i18n fallback and key lookup
- [x] Add tests for default language persistence and language changes per chat
- [x] Add tests for job-language snapshot behavior
- [x] Add tests for on-demand translation behavior without persisted translation caching (`tests/test_translation_service.py`)
- [x] Add tests for `ru`, `en`, and `es` formatter output (`tests/test_telegram_formatter.py`)
- [x] Add tests for `/language` command routing and webhook integration
- [x] Run full `python -m pytest -q` — 486 passed

## Follow-Up

- [ ] Decide whether translated outputs should later be precomputed asynchronously for hot languages
- [ ] Decide whether to reuse translated structured blocks across future non-Telegram channels
