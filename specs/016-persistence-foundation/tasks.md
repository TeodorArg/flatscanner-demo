# Tasks 016 — Persistence Foundation

## Legend
- [ ] pending
- [x] done

---

## Implementation

- [x] Create `specs/016-persistence-foundation/` (spec.md, plan.md, tasks.md)
- [x] Add `src/domain/user.py` — `TelegramUser` Pydantic model
- [x] Append `UserRow` + `ChatSettingsRow` to `src/storage/models.py`
- [x] Create `src/storage/db.py` — async engine helpers + `create_tables`
- [x] Append `UserRepository` + `ChatSettingsRepository` to `src/storage/repository.py`
- [x] Create `src/storage/sqlalchemy_repos.py` — concrete implementations
- [x] Add `asyncpg` / `aiosqlite` to `pyproject.toml`
- [x] Update `src/app/main.py` lifespan to wire up DB engine

## Tests

- [x] Extend `tests/test_storage_models.py` — structural tests for new ORM models
- [x] Create `tests/test_persistence_repos.py` — SQLite-backed repo tests
- [x] All existing tests still pass

## Docs

- [ ] Update `docs/project/backend/backend-docs.md` if implementation decisions
      affect future contributors (deferred — no architectural surprises)

## PR

- [x] Open PR against `main` — PR #33
- [x] Wait for `baseline-checks`, `guard`, `python-checks`, and `AI Review` — all passed on current head SHA
