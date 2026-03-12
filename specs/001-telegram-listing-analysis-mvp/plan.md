# Implementation Plan: Telegram Listing Analysis MVP

## Summary

Build a backend-first vertical slice where Telegram receives a listing URL, the system selects a source adapter, collects Airbnb data through Apify, normalizes the listing, enriches it with a minimal initial signal set, and returns an explainable AI summary through Telegram.

## Files And Areas

- `src/` for Telegram bot, FastAPI services, background jobs, adapters, schemas, and analysis modules
- `tests/` for unit and integration coverage of adapter routing, normalization, analysis orchestration, and Telegram formatting
- `docs/project/backend/backend-docs.md` for durable backend context
- `docs/adr/001-backend-mvp-architecture.md` for the stack decision
- `specs/001-telegram-listing-analysis-mvp/` for feature execution artifacts

## Proposed Backend Shape

- `src/app/` for FastAPI bootstrap and shared configuration
- `src/telegram/` for bot command handling and message formatting
- `src/adapters/` for source platform detection and parsing adapters
- `src/domain/` for normalized listing models and scoring inputs
- `src/enrichment/` for external context providers
- `src/analysis/` for OpenRouter prompting, orchestration, and price fairness logic
- `src/jobs/` for background processing workers
- `src/storage/` for persistence models and repositories

## Initial Data Flow

1. Telegram receives a message with a URL
2. URL classifier identifies the listing provider
3. A job record is created and queued
4. The Airbnb adapter fetches raw data from Apify
5. Raw payload is mapped into a normalized listing schema
6. Minimal enrichments run against the location data that is available
7. AI summarization and price-fairness logic produce a result package
8. Telegram formats and sends the response

## Risks

- Some listings may not expose stable coordinates or enough data for strong enrichments
- External enrichment coverage will vary significantly by geography
- AI-generated price judgments may drift unless anchored to structured signals
- Telegram responses can become too long unless the output format is tightly scoped

## Validation

- Add automated tests for URL provider detection
- Add automated tests for Airbnb raw-to-normalized mapping
- Add automated tests for Telegram response formatting
- Add orchestration tests for partial enrichment success and failure cases

## Notes

The first version should prefer a small, reliable enrichment set over a broad but brittle one. Price fairness can start as a hybrid of explicit heuristics plus AI explanation rather than a purely model-generated score.
