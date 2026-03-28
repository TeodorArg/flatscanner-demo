# Backend Docs

## Current Default

- Language: Python
- API: FastAPI
- Primary interface: Telegram backed by FastAPI services
- Validation/settings: Pydantic
- Database: PostgreSQL
- Queue/cache: Redis

## Core Backend Shape (MVP)

- `src/telegram/`: message intake and response formatting
  - channel-specific progress + presenter implementations for Telegram delivery
- `src/web/`: placeholder web-channel contracts and stub API endpoints
  - `POST /web/submit` currently returns an explicit 501 placeholder
  - `GET /web/status/{job_id}` and `GET /web/result/{job_id}` are shape-only stubs
- `src/adapters/`: provider detection and source adapters
- `src/domain/`: normalized listing models
- `src/enrichment/`: external context providers
- `src/analysis/`: AI summarization and price-fairness logic
- `src/jobs/` and `src/storage/`: async execution and persistence
- `src/application/`: channel-neutral use-case layer (`submit_analysis_request`,
  `run_analysis_job`); all delivery channels must go through this layer instead
  of calling queue or processor modules directly

## Target Post-MVP Layer Model

See ADR 004 for the full decision. The planned layers in execution order:

1. **Ingestion & Adapter Layer** - URL detection, provider selection, adapter execution, raw payload capture
2. **Normalization Layer** - adapter output -> `ListingSnapshot`
3. **Analysis Module Framework** - module registry and runner; provider-specific + generic fallback per module. P3 now fronts the live analysis stage with a generic `AISummaryModule`, so future specialist modules can be added without replacing the delivery path again.
4. **Enrichment Layer** - transport, nearby places, safety (future), comparable prices (future)
5. **Result Assembly** - score aggregation, analysis cache lookup/write
6. **Formatter / Delivery Layer** - channel-specific presenters/serializers;
   Telegram now delivers final results through `TelegramAnalysisPresenter`;
   Web foundation currently exposes read models and no-op presenter/progress
   stubs until persistence-backed delivery lands
7. **Persistence Layer** - six bounded areas: Users, ChatSettings, Billing, AnalysisCache, RawPayloads, AnalysisResults

Migration is broken into phases P1-P7 in `specs/015-post-mvp-architecture-foundation/spec.md`.

## Integration Direction

- Airbnb is the first provider, but parsing must stay adapter-based.
- Apify is the default extraction source where supported.
  - Airbnb ingestion uses two specialized `tri_angle` actors (split introduced in spec 028):
    - **Listing actor** (`tri_angle/airbnb-rooms-urls-scraper`, default via `APIFY_AIRBNB_ACTOR_ID`):
      listing details, dated price data, photos, host, amenities, and rules.
      Replaced `curious_coder~airbnb-scraper` which could not reliably return priced output.
    - **Reviews actor** (`tri_angle/airbnb-reviews-scraper`, to be wired in spec 028 Slice 2):
      dedicated review corpus for the reviews analysis module.
  - `APIFY_API_TOKEN` is required in all non-development/testing environments and validated at startup.
  - The client authenticates using an `Authorization: Bearer <token>` header (not a query parameter).
- OpenRouter is the model gateway.
- Enrichment sources may vary by geography and must tolerate partial availability.
- Geoapify Places API is the first enrichment provider set (MVP):
  - **Transport provider** (`src/enrichment/providers/geoapify_transport.py`): fetches nearby public transport stops (subway, train, tram, bus, ferry) within 500 m of listing coordinates.
  - **Nearby places provider** (`src/enrichment/providers/geoapify_nearby_places.py`): fetches nearby POIs (supermarkets, restaurants, parks, pharmacies) within 500 m.
  - `GEOAPIFY_API_KEY` is required in all non-development/testing environments and validated at startup.
  - In development/testing, enrichment is skipped when the key is absent.
  - Geoapify Places currently authenticates via the `apiKey` query parameter rather than a bearer header, so future hardening should re-check this if the provider adds header-based auth.
  - Safety enrichment remains deferred for a future decision.
  - Enrichment results are threaded into the AI analysis prompt via `build_prompt(listing, enrichment)` so the model factors in local context.

## Design Constraints

- Keep provider-specific parsing separate from normalized domain logic.
- Prefer explainable scoring over LLM-only judgment.
- Keep cost-sensitive dependencies visible.
- Record durable backend changes in `docs/adr/`.
- Reusable analysis guidance belongs in repository skills under `skills/`; provider normalizers should feed unified corpus contracts before AI analysis runs.

## Delivery Infrastructure

- Automated review runs on a Windows self-hosted runner labeled `ai-runner`.
- Reviewer selection comes only from `AI_REVIEW_AGENT` and supports `claude` or `codex`, with `claude` as fallback.
- Runner setup lives in `docs/project/backend/self-hosted-runner.md`.
- Local Claude worker launches live in `docs/claude-worker-orchestration.md`.
- Docker-first VPS rollout guidance lives in `docs/project/backend/docker-mvp-deployment.md`.

## Open Decisions

- Redis worker library (still deferred; analysis module framework landed in P3)
- Regional safety providers (safety enrichment deferred from MVP)
- Raw/source payload retention policy: TTL, archival, or deletion strategy (storage backend was chosen in P2 as PostgreSQL-backed JSON payload storage)
- Comparable-listing strategy for price fairness (deferred to reviews/price module specs)
- Payment provider selection: Telegram Payments vs. external checkout (decided in P7 spec)
