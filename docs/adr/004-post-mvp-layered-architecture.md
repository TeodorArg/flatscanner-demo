# ADR 004: Post-MVP Layered Architecture

## Status

Accepted

## Context

The MVP ships a single linear analysis flow: URL → adapter → enrichment → AI summary → Telegram response. The product direction requires this to grow into a system with multiple listing providers, multiple analysis modules (reviews, price, host, location, amenities, policies), durable user identity, configurable settings, billing and entitlement enforcement, analysis result caching, and stored raw source payloads.

Adding all of this directly to the existing flow without explicit boundaries would produce an unmaintainable monolith and make provider and module additions error-prone.

ADR 001 established the MVP stack (Python, FastAPI, PostgreSQL, Redis, Telegram, OpenRouter, Apify). This ADR defines the next-layer architecture that builds on that stack.

## Decision

Adopt a layered architecture with the following layers and responsibilities:

**Ingestion & Adapter Layer** — URL detection, provider selection, adapter execution, and raw payload capture. Adapters are provider-specific. Raw adapter output is written to the raw payload store before any transformation.

**Normalization Layer** — Converts provider-specific adapter output into a shared `ListingSnapshot` domain model. All downstream layers operate only on `ListingSnapshot`.

**Analysis Module Framework** — A registry and runner for named analysis modules. Each module may have a provider-specific implementation and a generic fallback. The runner prefers provider-specific when available. Module outputs are typed result objects merged by the framework.

**Enrichment Layer** — Independently replaceable enrichment providers (transport, nearby places, safety, comparable prices). Partial failures are tolerated; the layer continues with available data.

**Result Assembly** — Merges module outputs and enrichment into a final `AnalysisResult`. Checks the analysis cache before running modules and writes the result to cache after.

**Formatter / Delivery Layer** — Converts `AnalysisResult` into channel-specific output. Telegram formatter is first; future formatters are added here.

**Persistence Layer** — Six bounded areas: Users, ChatSettings, Billing, AnalysisCache, RawPayloads, AnalysisResults.

## Migration Path

The migration from MVP to the target architecture is broken into seven independent phases:

| Phase | Name |
|---|---|
| P1 | Persistence foundation — users and chat_settings DB schema |
| P2 | Raw payload capture — raw_payloads store, written before normalization |
| P3 | Analysis module framework — registry, runner, typed results |
| P4 | Reviews analysis module — Airbnb-specific and generic variants |
| P5 | Analysis result cache — cache lookup before run, write after |
| P6 | Billing foundation — plans, subscriptions, entitlements schema |
| P7 | Payment integration — connect billing to a payment provider |

Each phase is independently shippable. P1 must precede P6; all other phases are loosely ordered.

## Consequences

- New listing providers require only a new adapter and, optionally, new provider-specific module variants; generic modules continue to work without changes.
- New analysis modules are added to the registry without modifying the runner or other modules.
- Raw payloads decouple debugging and reanalysis from adapter implementation.
- The persistence layer boundaries prevent a single catch-all table approach.
- The phased migration keeps the MVP flow operational throughout; no big-bang rewrite is required.
- Open decisions deferred to phase specs: raw payload storage backend (PostgreSQL JSONB vs. object storage), job queue library, payment provider.
