# Plan: Multilingual Bot Output

## Summary

Add multilingual Telegram output without duplicating the entire analysis pipeline per language. The implementation will keep canonical AI-generated freeform analysis blocks in English, persist a per-chat language preference, snapshot the language onto each queued job, translate freeform blocks on demand, cache those translations, and format final Telegram replies with localized labels and system strings.

## Architecture Direction

- Add `src/i18n/` for static bot/system strings and language helpers
- Add a `Language` enum with `ru`, `en`, `es`
- Persist Telegram chat language preference separately from analysis results
- Extend `AnalysisJob` with `language`
- Keep canonical analysis result blocks in English
- Add a translation service for `summary`, `strengths[]`, `risks[]`, and `price_explanation`
- Cache translated structured blocks by `(analysis_id or canonical_result_hash, target_language, translation_version, model)`
- Keep the formatter pure: it receives already translated blocks plus localized labels

## Files And Areas

- `src/i18n/`
- `src/telegram/router.py`
- `src/telegram/formatter.py`
- `src/telegram/dispatcher.py`
- `src/domain/listing.py`
- `src/analysis/service.py`
- `src/jobs/processor.py`
- `src/storage/`
- `src/app/config.py`
- `tests/`

## Risks

- Mixing translation work into the formatter would make caching and testing harder
- If chat language is not snapshotted onto the job, in-flight responses may come back in the wrong language
- If canonical analysis storage becomes language-specific, cache reuse and prompt maintenance will get much harder
- Translation caching must be tied to the canonical result content/version, not just the listing URL

## Validation

- Add unit tests for i18n catalog lookup and fallback to Russian
- Add router tests for default language and language-change flow
- Add job tests for enqueue-time language snapshotting
- Add translation service tests for structured block translation behavior and cache hits
- Add formatter tests for `ru`, `en`, and `es`
- Run `python -m pytest -q`

## Notes

- Static UI/system strings are i18n-owned
- Freeform AI-generated blocks are translation-stage owned
- Final message assembly remains formatter-owned
