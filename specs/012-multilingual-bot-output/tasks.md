# Tasks: Multilingual Bot Output

## Spec

- [x] Define the canonical-English plus translated-output architecture
- [x] Capture the supported languages and default-language behavior
- [x] Record the language snapshot requirement for queued jobs

## Design

- [ ] Define the `Language` enum and centralized i18n catalog structure
- [ ] Define storage for Telegram chat language preference
- [ ] Define the translation cache key and invalidation/versioning rules
- [ ] Decide the first translation model/provider for MVP multilingual output
- [ ] Decide the UX for language switching in Telegram (`/language`, buttons, or hybrid)

## Implementation

- [ ] Add `src/i18n/` with language types, catalog, and translator helper
- [ ] Add a Telegram chat language preference model/repository
- [ ] Extend `AnalysisJob` with `language`
- [ ] Snapshot the effective language when enqueueing an analysis job
- [ ] Localize immediate Telegram replies (`help`, `unsupported`, `analysing`, language-change acknowledgements)
- [ ] Keep `AnalysisService` canonical output in English for generated freeform blocks
- [ ] Add a translation service for structured freeform result blocks
- [ ] Add translation caching for translated result blocks
- [ ] Update the formatter to render localized labels and consume translated blocks
- [ ] Add language switching flow in Telegram

## Validation

- [ ] Add tests for i18n fallback and key lookup
- [ ] Add tests for default language persistence and language changes per chat
- [ ] Add tests for job-language snapshot behavior
- [ ] Add tests for translation cache hit/miss behavior
- [ ] Add tests for `ru`, `en`, and `es` formatter output
- [ ] Run full `python -m pytest -q`

## Follow-Up

- [ ] Decide whether translated outputs should later be precomputed asynchronously for hot languages
- [ ] Decide whether to reuse translated structured blocks across future non-Telegram channels
