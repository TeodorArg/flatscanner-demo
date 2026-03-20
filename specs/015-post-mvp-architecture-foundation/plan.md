# Plan: Post-MVP Architecture Foundation

## Approach

This is a documentation-only task. No runtime code is changed.

The deliverables are:

1. `specs/015-post-mvp-architecture-foundation/` — spec, plan, tasks.
2. `docs/adr/004-post-mvp-layered-architecture.md` — durable ADR for the layered architecture decision.
3. `docs/project/backend/backend-docs.md` — updated to reflect post-MVP layer model and open decisions resolved.

## Touched Areas

| Area | Change |
|---|---|
| `specs/015-post-mvp-architecture-foundation/` | New feature folder (this task) |
| `docs/adr/004-post-mvp-layered-architecture.md` | New ADR |
| `docs/project/backend/backend-docs.md` | Add post-MVP architecture section and update open decisions |

No files under `src/`, `tests/`, or `.github/` are modified.

## Key Decisions Recorded

### Layered architecture over a growing monolith
The MVP analysis flow is a single code path. Adding modules and providers to it directly would create an unmaintainable blob. The layered model creates explicit boundaries that let modules and providers evolve independently.

### Analysis module framework with provider-specific + generic fallback
Requiring a provider-specific module for every new provider would block generic provider support. The framework runner prefers provider-specific but falls back to generic, so generic support is available immediately for any new adapter.

### Raw payload capture before normalization
Storing raw adapter output before transformation decouples debugging and reanalysis from adapter implementation. It also allows retroactive reprocessing when analysis modules change.

### Six persistence areas
Users, ChatSettings, Billing, AnalysisCache, RawPayloads, and AnalysisResults are separated by bounded purpose. This prevents a single catch-all table approach that would create hidden coupling.

### Phased migration (P1–P7)
Each phase is independently shippable and testable. Phases do not need to be completed in the same PR or sprint. This avoids a big-bang rewrite and keeps the MVP flow functional throughout.

## Risks

| Risk | Mitigation |
|---|---|
| Phase ordering creates hidden dependencies | P1 (persistence foundation) must precede P6 (billing); all other phases are loosely ordered |
| Raw payload storage cost | P2 spec will decide between PostgreSQL JSONB and object storage based on expected payload size |
| Module framework over-engineering | Keep the registry and runner as simple as possible in P3; do not add plugin loading or dynamic discovery in the first pass |
| Billing scope creep | P6 covers schema and entitlement checks only; P7 is the payment wiring; keep them separate |

## Validation

- No runtime code is added, so no tests to run.
- Validate that all markdown files render cleanly (no broken headers or tables).
- Confirm the ADR numbering does not conflict with existing ADRs.
- Confirm the spec folder naming matches the `015` branch identifier.
