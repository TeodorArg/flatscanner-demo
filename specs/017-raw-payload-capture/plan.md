# Plan 017 — Raw Payload Capture

## Approach

Minimal-footprint additions that follow the patterns established in P1 (016).
No existing public API is removed — `AdapterResult` replaces the raw
`NormalizedListing` return type of `fetch()`, so callers are updated in-place.

## File-by-file changes

### New files
| File | Purpose |
|---|---|
| `src/domain/raw_payload.py` | `RawPayload` Pydantic model |
| `tests/test_raw_payload_capture.py` | Focused integration + unit tests for P2 |

### Modified files
| File | Change |
|---|---|
| `src/adapters/base.py` | Add `AdapterResult` dataclass; change `fetch()` return type |
| `src/adapters/airbnb.py` | `fetch()` returns `AdapterResult(raw=items[0], listing=...)` |
| `src/storage/models.py` | Append `RawPayloadRow` ORM class |
| `src/storage/repository.py` | Append `RawPayloadRepository` Protocol |
| `src/storage/sqlalchemy_repos.py` | Append `SQLAlchemyRawPayloadRepository` |
| `src/jobs/processor.py` | Add `raw_payload_repo` param; persist after fetch |
| `tests/test_airbnb_extraction.py` | Update assertions for `AdapterResult` return type |
| `tests/test_job_processor.py` | Update mock adapters to return `AdapterResult` |
| `tests/test_storage_models.py` | Add `RawPayloadRow` structural tests |
| `tests/test_persistence_repos.py` | Add `SQLAlchemyRawPayloadRepository` tests |

## Key decisions

1. **`AdapterResult` is a dataclass** (not Pydantic) — it is an internal
   transport type, not a domain model. `raw` is `dict[str, Any]`; no schema
   validation is needed here.
2. **No upsert for raw payloads** — each fetch is a distinct capture event;
   idempotency is not required.
3. **Save errors are swallowed** — raw payload persistence is best-effort.
   A logging warning is emitted but the analysis pipeline continues.
4. **PostgreSQL JSONB via SQLAlchemy JSON column** — same as `ListingRow.raw_payload`.
5. **No alembic migration** — `create_tables` covers development; production
   migration tooling is deferred (same policy as P1).
