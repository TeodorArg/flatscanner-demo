# Plan 016 — Persistence Foundation

## Approach
Minimal, additive changes only.  Every new file is in `src/storage/` or
`src/domain/`; the one app-wiring change is isolated to the lifespan in
`src/app/main.py`.

## Step-by-step

### 1 — Domain model: `TelegramUser`
Create `src/domain/user.py`.
- Pydantic `BaseModel` with fields matching the spec.
- Mirrors the pattern of `NormalizedListing` in `src/domain/listing.py`.

### 2 — ORM models: `UserRow` + `ChatSettingsRow`
Append to `src/storage/models.py`.
- Both use the existing `Base` and `_utcnow` helpers.
- `UserRow` UNIQUE on `telegram_user_id`.
- `ChatSettingsRow` uses `chat_id` (BigInteger) as primary key.

### 3 — DB infrastructure: `src/storage/db.py`
New file.  Exports:
- `make_engine(database_url, **kwargs) -> AsyncEngine`
- `make_session_factory(engine) -> async_sessionmaker[AsyncSession]`
- `create_tables(engine) -> None`
No global singletons; callers own the engine lifecycle.

### 4 — Repository protocols
Append `UserRepository` and `ChatSettingsRepository` to
`src/storage/repository.py`.

### 5 — Concrete SQLAlchemy implementations
New file `src/storage/sqlalchemy_repos.py`.
- `SQLAlchemyUserRepository(session: AsyncSession)`
- `SQLAlchemyChatSettingsRepository(session: AsyncSession)`
Both use `session.merge()` for upserts.

### 6 — Dependencies
Add `asyncpg>=0.29.0` to `[project].dependencies` (runtime).
Add `aiosqlite>=0.20.0` to `[project.optional-dependencies].dev` (tests only).

### 7 — App lifespan
Update `src/app/main.py` lifespan to:
- Create an `AsyncEngine` via `make_engine(settings.database_url)`.
- Store it in `app.state.engine`.
- Dispose it on shutdown.
Does NOT call `create_tables()` (that is a deploy/migration-time operation).

### 8 — Tests
- Extend `tests/test_storage_models.py` with structural tests for
  `UserRow` and `ChatSettingsRow`.
- Add `tests/test_persistence_repos.py` with concrete repo tests backed by
  `sqlite+aiosqlite:///:memory:`.
- Add bootstrap tests for DB engine wiring in `tests/test_app_bootstrap.py`.

## Risks and mitigations
| Risk | Mitigation |
|---|---|
| asyncpg not installed in some environments | Listed as hard dependency; tests use aiosqlite |
| SQLite ≠ PostgreSQL (no timezone, UUID as TEXT) | Tests cover behaviour, not exact types |
| `create_tables` called twice in tests | `checkfirst=True` is SQLAlchemy default for `create_all` |
| Existing test `test_database_url_default_is_driver_agnostic` | `make_engine` converts the URL; config default stays as `postgresql://` |
