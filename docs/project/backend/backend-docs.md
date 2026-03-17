# Backend Docs

## Current Default

- Language: Python
- API: FastAPI
- Primary interface: Telegram backed by FastAPI services
- Validation/settings: Pydantic
- Database: PostgreSQL
- Queue/cache: Redis

## Core Backend Shape

- `src/telegram/`: message intake and response formatting
- `src/adapters/`: provider detection and source adapters
- `src/domain/`: normalized listing models
- `src/enrichment/`: external context providers
- `src/analysis/`: AI summarization and price-fairness logic
- `src/jobs/` and `src/storage/`: async execution and persistence

## Integration Direction

- Airbnb is the first provider, but parsing must stay adapter-based.
- Apify is the default extraction source where supported.
  - Default Airbnb actor: `dtrungtin~airbnb-scraper` (overridable via `APIFY_AIRBNB_ACTOR_ID`).
  - `APIFY_API_TOKEN` is required in all non-development/testing environments and validated at startup.
  - The client authenticates using an `Authorization: Bearer <token>` header (not a query parameter).
- OpenRouter is the model gateway.
- Enrichment sources may vary by geography and must tolerate partial availability.
- Geoapify Places API is the first enrichment provider set (MVP):
  - **Transport provider** (`src/enrichment/providers/geoapify_transport.py`): fetches nearby public transport stops (subway, train, tram, bus, ferry) within 500 m of listing coordinates.
  - **Nearby places provider** (`src/enrichment/providers/geoapify_nearby_places.py`): fetches nearby POIs (supermarkets, restaurants, parks, pharmacies) within 500 m.
  - Both providers require `GEOAPIFY_API_KEY` in settings; enrichment is silently skipped when the key is absent.
  - Safety enrichment remains deferred for a future decision.
  - Enrichment results are threaded into the AI analysis prompt via `build_prompt(listing, enrichment)` so the model factors in local context.

## Design Constraints

- Keep provider-specific parsing separate from normalized domain logic.
- Prefer explainable scoring over LLM-only judgment.
- Keep cost-sensitive dependencies visible.
- Record durable backend changes in `docs/adr/`.

## Delivery Infrastructure

- Automated review runs on a Windows self-hosted runner labeled `ai-runner`.
- Reviewer selection comes only from `AI_REVIEW_AGENT` and supports `claude` or `codex`, with `claude` as fallback.
- Runner setup lives in `docs/project/backend/self-hosted-runner.md`.
- Local Claude worker launches live in `docs/claude-worker-orchestration.md`.

## Open Decisions

- Redis worker library
- Regional safety providers (safety enrichment deferred from MVP)
- Long-term source payload retention
- Comparable-listing strategy for price fairness
