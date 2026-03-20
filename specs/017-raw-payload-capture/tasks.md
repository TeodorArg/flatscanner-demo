# Tasks 017 - Raw Payload Capture

## Legend
- [ ] pending
- [x] done

## Spec
- [x] Create `specs/017-raw-payload-capture/` (spec.md, plan.md, tasks.md)

## Implementation
- [x] Add `AdapterResult` dataclass + update `fetch()` in `src/adapters/base.py`
- [x] Update `AirbnbAdapter.fetch()` to return `AdapterResult`
- [x] Add `RawPayload` Pydantic model in `src/domain/raw_payload.py`
- [x] Append `RawPayloadRow` to `src/storage/models.py`
- [x] Append `RawPayloadRepository` Protocol to `src/storage/repository.py`
- [x] Append `SQLAlchemyRawPayloadRepository` to `src/storage/sqlalchemy_repos.py`
- [x] Wire `raw_payload_repo` param into `src/jobs/processor.py`
- [x] Wire DB-backed `raw_payload_repo` into `src/jobs/worker.py` (`process_once`, `run_worker`) via `session_factory`
- [x] Create engine + `session_factory` once in `src/jobs/cli.py` (`run_worker_process`); dispose on exit

## Tests
- [x] Update `tests/test_airbnb_extraction.py` for `AdapterResult` return type
- [x] Update `tests/test_job_processor.py` mocks for `AdapterResult`
- [x] Extend `tests/test_storage_models.py` with `RawPayloadRow` structural tests
- [x] Extend `tests/test_persistence_repos.py` with `SQLAlchemyRawPayloadRepository` tests
- [x] Create `tests/test_raw_payload_capture.py` - focused P2 tests
- [x] Extend `tests/test_raw_payload_capture.py` with worker/CLI wiring tests (`TestProcessOnceWorkerWiring`, `TestRunWorkerProcessDBWiring`)
- [x] Update `tests/test_worker_cli.py` for new `session_factory` kwarg
- [x] All existing tests pass (739/739)

## PR
- [x] Open PR against `main` (#34)
- [x] Wait for `baseline-checks`, `guard`, `python-checks`, and `AI Review`
