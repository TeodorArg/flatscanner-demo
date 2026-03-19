# Tasks: Multilingual Bot Output

## Spec

- [x] Define the canonical-English plus translated-output architecture
- [x] Capture the supported languages and default-language behavior
- [x] Record the language snapshot requirement for queued jobs
- [x] Record the approved decision: translated outputs are generated on demand and not persisted as cache artifacts

## Design

- [x] Define the `Language` enum and centralized i18n catalog structure
- [x] Define storage for Telegram chat language preference
- [ ] Define how on-demand translation is invoked without creating a persisted translation cache layer
- [ ] Decide the first translation model/provider for MVP multilingual output
- [ ] Decide the UX for language switching in Telegram (`/language`, buttons, or hybrid)

## Implementation

- [x] Add `src/i18n/` with language types, catalog, and `get_string` helper
- [x] Add `src/storage/chat_preferences.py` — Redis-backed chat language preference repository
- [x] Extend `AnalysisJob` with `language` (defaults to `DEFAULT_LANGUAGE`)
- [x] Snapshot the effective language when enqueueing an analysis job
- [x] Localize immediate Telegram replies (`help`, `unsupported`, `analysing`) via i18n catalog
- [ ] Keep `AnalysisService` canonical output in English for generated freeform blocks
- [ ] Add a translation service for structured freeform result blocks
- [ ] Keep translated output ephemeral; do not persist it as a multilingual cache artifact
- [ ] Update the formatter to render localized labels and consume translated blocks
- [ ] Add language switching flow in Telegram

## Validation

- [x] Add tests for i18n fallback and key lookup
- [x] Add tests for default language persistence and language changes per chat
- [x] Add tests for job-language snapshot behavior
- [ ] Add tests for on-demand translation behavior without persisted translation caching
- [ ] Add tests for `ru`, `en`, and `es` formatter output
- [x] Run full `python -m pytest -q`

## Follow-Up

- [ ] Decide whether translated outputs should later be precomputed asynchronously for hot languages
- [ ] Decide whether to reuse translated structured blocks across future non-Telegram channels
