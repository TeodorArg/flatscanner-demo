# Backend Docs

## Status

Initial backend direction is chosen and should be treated as the current default unless replaced by a newer ADR.

## Runtime And Framework

- Language: Python
- API framework: FastAPI
- Primary interface in the first release: Telegram bot backed by FastAPI services
- Validation and settings: Pydantic

## Core Services

- Telegram interface layer for receiving listing URLs and returning analysis results
- Listing ingestion layer with platform adapters
- Enrichment layer for geospatial and public-context signals
- AI analysis layer using OpenRouter-backed models
- Scoring layer for listing quality and price fairness
- Background job workers for long-running parsing and enrichment flows

## Storage And Jobs

- Primary database: PostgreSQL
- Queue/cache: Redis
- Background processing: Redis-backed worker system to be finalized in implementation planning

## Integration Direction

- Listing parsing starts with Airbnb but must use an adapter pattern so other aggregators can be added without rewriting the rest of the pipeline
- Apify is the default source for listing extraction where supported
- OpenRouter is the model gateway for AI summarization and reasoning
- External enrichments may include Street View, nearby places, transport access, and public safety data depending on regional availability

## Suggested Domain Flow

1. Accept listing URL from Telegram
2. Detect platform and enqueue an analysis job
3. Fetch raw listing data through the matching adapter
4. Normalize listing data into a shared schema
5. Run enrichment providers against coordinates or inferred location
6. Build an explainable AI summary and scoring package
7. Persist the job, inputs, derived signals, and final result
8. Return a concise and structured report to Telegram

## Design Constraints

- Keep source-specific parsing logic separate from normalized domain logic
- Treat external data availability as unreliable and support partial results
- Prefer explainable scoring over LLM-only judgment
- Keep cost controls visible because Apify, Google, and OpenRouter usage can scale quickly
- Record notable architecture changes in `docs/adr/`

## Delivery Infrastructure

- Automated PR review runs on a Windows self-hosted GitHub runner labeled `codex`
- The runner invokes a local Codex adapter script so review can use the machine-local Codex setup
- Setup instructions live in `docs/project/backend/self-hosted-runner.md`
- Codex may also launch local Claude CLI workers on the same machine through isolated git worktrees
- Claude worker orchestration instructions live in `docs/claude-worker-orchestration.md`

## What Belongs Here

Record stable backend decisions when they are made:

- runtime and framework
- database choice
- authentication model
- API conventions
- background jobs
- commands for local development and testing

## Open Decisions

- Which Redis-backed worker library to standardize on
- Which safety/crime data sources are reliable enough by region
- Whether comparable listings for price fairness will come from the same source platform, a separate dataset, or both
- Whether raw source payloads and derived media metadata should be stored long term or pruned
