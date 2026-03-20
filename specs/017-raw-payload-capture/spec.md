# Spec 017 — Raw Payload Capture (P2)

## Status
Active — implementation in progress on branch `codex/claude-017-raw-payload-capture-raw-payload-capture`

## Context
Feature 015 defined a phased migration from the MVP monolith to a layered
architecture (ADR 004). Phase 2 (P2) is raw payload capture: persist the raw
adapter response before any normalisation so that it can be replayed for
debugging, schema changes, or reanalysis without re-fetching from Apify.

Feature 016 (P1) delivered the DB engine, session factory, and repository
patterns for Users and ChatSettings. P2 builds on that foundation.

The storage backend decision (open in 015/backend-docs): **PostgreSQL JSONB**
via the same SQLAlchemy async infrastructure established in P1.  Object storage
(S3/R2) is deferred until payload volumes justify it.

## Goals
1. Dedicated `raw_payloads` table with a UUID PK, provider, source URL,
   optional source ID, JSON payload, and `captured_at` timestamp.
2. `RawPayload` Pydantic domain model mirroring the table.
3. `RawPayloadRepository` Protocol and `SQLAlchemyRawPayloadRepository`
   concrete implementation.
4. `AdapterResult` dataclass returned by `ListingAdapter.fetch()` carrying
   both `raw: dict` and `listing: NormalizedListing`.
5. `AirbnbAdapter.fetch()` conforms to the new contract.
6. `process_job` in `src/jobs/processor.py` accepts an optional
   `raw_payload_repo` parameter and persists the raw payload after fetch when
   the repo is present.
7. All existing tests continue to pass; new focused tests cover the ORM model,
   repository, adapter contract, and processor wiring.

## Out of scope
- Analysis module framework (P3, feature 018).
- Raw payload retention / TTL policy (open decision).
- Replaying a raw payload through the normalisation pipeline.
- Any changes to billing or enrichment layers.

## Storage decision
Raw payloads are stored in PostgreSQL (JSONB via SQLAlchemy `JSON` column),
matching the existing storage stack. Object storage is not introduced in this
phase.

## Domain model

### `RawPayload` (src/domain/raw_payload.py)
```
id:          UUID (PK, default uuid4)
provider:    str
source_url:  str
source_id:   str | None
payload:     dict[str, Any]
captured_at: datetime (UTC)
```

## Persistence model

### `RawPayloadRow` (table: `raw_payloads`)
Mirrors `RawPayload`. No foreign key to `listings` — capture happens before
normalisation so no listing row exists yet.

```
id:          Uuid  PK
provider:    String(64)  NOT NULL
source_url:  Text  NOT NULL
source_id:   String(256)  nullable
payload:     JSON  NOT NULL
captured_at: DateTime(timezone=True)  NOT NULL
```

## Adapter contract

### `AdapterResult` (src/adapters/base.py)
```python
@dataclass
class AdapterResult:
    raw: dict[str, Any]
    listing: NormalizedListing
```

`ListingAdapter.fetch()` now returns `AdapterResult`.

`AirbnbAdapter.fetch()` wraps the Apify response item as `raw` and the
`_normalize()` output as `listing`.

## Repository contract

### RawPayloadRepository (Protocol)
```
save(payload: RawPayload) -> None          # insert; no upsert needed
get_by_id(payload_id: UUID) -> RawPayload | None
```

## Processor wiring

```
process_job(job, settings, *, ..., raw_payload_repo=None)
```

After `adapter.fetch()`:
1. Extract `adapter_result.listing` for the analysis pipeline.
2. If `raw_payload_repo` is not None, construct a `RawPayload` from
   `adapter_result.raw` and call `raw_payload_repo.save()`.
3. Persist errors from `save()` are logged and swallowed (never block
   the analysis pipeline).

## Validation
- Structural tests for `RawPayloadRow` (metadata inspection, no DB needed).
- Integration tests for `SQLAlchemyRawPayloadRepository` using SQLite in-memory.
- Adapter contract tests: `AirbnbAdapter.fetch()` returns `AdapterResult`.
- Processor tests: raw payload saved when repo provided; skipped when None;
  save errors do not propagate.
