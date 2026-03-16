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
- OpenRouter is the model gateway.
- Enrichment sources may vary by geography and must tolerate partial availability.

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
- regional safety and public-context providers
- long-term source payload retention
- comparable-listing strategy for price fairness
