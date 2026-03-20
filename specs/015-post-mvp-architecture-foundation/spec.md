# Feature Spec: Post-MVP Architecture Foundation

## Context

The MVP delivers a single end-to-end flow: URL → adapter → enrichment → AI summary → Telegram response. This works for the first release but does not scale to the planned product direction:

- Multiple analysis modules (reviews, price, host, location, amenities, policies)
- Multiple listing providers (Airbnb, Booking.com, generic fallback)
- Durable user identity, configurable chat settings, billing, and plan enforcement
- Cached analysis results to avoid redundant work and API cost
- Stored raw source payloads for debugging and reanalysis

This spec defines the target post-MVP layered architecture and the migration path from the MVP monolith to it. No runtime code is produced in this task; the output is the architecture baseline from which follow-up specs are derived.

## Scope

- Define the target layer model and the responsibilities of each layer.
- Define how provider-specific analyzers and generic analyzers coexist.
- Define the persistence schema boundaries (users, settings, billing, cache, raw payloads).
- Break the migration into small, named implementation phases suitable for individual feature specs.
- Update durable docs and create a new ADR.

## Out Of Scope

- Implementing any runtime code, database migrations, or schema files.
- Billing provider wiring or payment integration runtime logic.
- Selecting a specific job queue library (deferred to a later spec).
- Non-Telegram delivery channels.

## Target Layered Architecture

```
┌─────────────────────────────────────┐
│        Delivery / Channels          │  Telegram, future: web, API
├─────────────────────────────────────┤
│       Message Router                │  command dispatch, screen routing
├─────────────────────────────────────┤
│       Ingestion & Adapter Layer     │  URL detection, provider selection,
│                                     │  adapter execution, raw payload capture
├─────────────────────────────────────┤
│       Normalization Layer           │  adapter output → ListingSnapshot
├─────────────────────────────────────┤
│       Analysis Module Framework     │  module registry, runner, result merge
│  ┌──────────┬─────────┬──────────┐  │
│  │ Reviews  │  Price  │  Host    │  │  per-module: provider-specific +
│  │ Location │  Amens  │ Policies │  │  generic fallback
│  └──────────┴─────────┴──────────┘  │
├─────────────────────────────────────┤
│       Enrichment Layer              │  transport, nearby places, safety (future),
│                                     │  comparable prices (future)
├─────────────────────────────────────┤
│       Result Assembly               │  score aggregation, cache lookup/write
├─────────────────────────────────────┤
│       Formatter / Delivery          │  Telegram formatter, future formatters
├─────────────────────────────────────┤
│       Persistence Layer             │  users, settings, billing, cache,
│                                     │  raw payloads, analysis results
└─────────────────────────────────────┘
```

## Layer Responsibilities

### Ingestion & Adapter Layer
- Detect listing provider from URL.
- Select and run the matching provider adapter (Airbnb via Apify, Booking.com, generic).
- Capture raw adapter response to the raw payload store before any transformation.
- Return raw payload reference + parsed output to the normalization layer.

### Normalization Layer
- Convert provider-specific raw output into a shared `ListingSnapshot` domain model.
- `ListingSnapshot` is the only contract downstream layers consume.

### Analysis Module Framework
- Registry of named analysis modules (reviews, price, host, location, amenities, policies).
- Each module declares: supported providers, a provider-specific implementation path, and a generic fallback.
- Runner invokes all or selected modules against a `ListingSnapshot` + enrichment context.
- Module outputs are typed result objects; the framework merges them.

### Provider-Specific vs. Generic Analyzers
- A module may register a provider-specific variant (e.g., `reviews.airbnb`) and a generic variant (`reviews.generic`).
- The runner prefers provider-specific when available; falls back to generic otherwise.
- Generic variants use only data present in `ListingSnapshot` and enrichment.
- New providers require only a new adapter + (optionally) new provider-specific module variants; existing generic modules continue to work.

### Enrichment Layer
- Remains as-is for MVP enrichment providers (transport, nearby places).
- Enrichment providers are independently replaceable and partial-failure-tolerant.
- Future additions: safety signals, comparable price feeds.

### Result Assembly
- Merge analysis module outputs and enrichment into a final `AnalysisResult`.
- Check analysis result cache before running modules; write result to cache after.
- Produce a structured, serializable result for the formatter.

### Persistence Layer
Six bounded areas:

| Area | Purpose |
|---|---|
| Users | Registration, identity, Telegram user mapping |
| ChatSettings | Per-chat language, analysis preferences, stored bot state |
| Billing | Plans, subscriptions, entitlements, payment records |
| AnalysisCache | Keyed by listing fingerprint; TTL-based invalidation |
| RawPayloads | Raw adapter responses, referenced by listing + provider + timestamp |
| AnalysisResults | Persisted assembled results linked to user + listing |

## Migration Phases

Each phase is an independent implementation slice that can become its own feature spec.

| Phase | Name | Scope |
|---|---|---|
| P1 | Persistence foundation | PostgreSQL schema for users and chat_settings; migrate in-memory chat settings to DB |
| P2 | Raw payload capture | Add raw_payloads table/store; write adapter output before normalization |
| P3 | Analysis module framework | Module registry, runner, typed result objects; refactor existing analysis into first module |
| P4 | Reviews analysis module | Implement reviews module with Airbnb-specific and generic variants |
| P5 | Analysis result cache | Add analysis_cache table; cache lookup before run, write after |
| P6 | Billing foundation | Plans, subscriptions, entitlements schema; entitlement checks at analysis entry point |
| P7 | Payment integration | Connect billing foundation to a payment provider (Telegram Payments or external) |

## Acceptance Criteria

- ADR 004 is written and documents the post-MVP layered architecture decision.
- `docs/project/backend/backend-docs.md` reflects the target layer model.
- `specs/015-post-mvp-architecture-foundation/` contains spec, plan, and tasks.
- No production runtime code is added in this task.
- Migration phases P1–P7 are documented and can each be opened as a standalone spec.

## Open Questions

- Whether raw payloads are stored in PostgreSQL (JSONB) or in object storage (S3/R2); decided in P2 spec.
- Which job queue library handles background analysis (deferred until P3).
- Whether billing uses Telegram Payments or an external checkout link; decided in P7 spec.
