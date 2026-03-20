# Spec 016 — Persistence Foundation

## Status
Active — implementation in progress

## Context
Feature 015 documented a phased migration from the MVP monolith to a layered
architecture (ADR 004). Phase 1 (P1) of that plan is the persistence foundation:
introduce durable database-backed storage for the two bounded areas that are
needed before any later phase can proceed — Users and ChatSettings.

The MVP already has SQLAlchemy ORM models for `ListingRow` and `AnalysisJobRow`,
a protocol-only repository layer, and Redis-backed chat settings. This feature
builds on that foundation without breaking any existing behaviour.

## Goals
1. Durable SQLAlchemy async infrastructure (engine, session factory, `create_tables`).
2. Telegram-linked user identity: `TelegramUser` domain model + `UserRow` ORM model.
3. Persisted chat settings: `ChatSettingsRow` ORM model that can sit alongside or
   eventually replace the Redis-backed `chat_preferences` layer.
4. Repository interfaces (`UserRepository`, `ChatSettingsRepository`) and concrete
   SQLAlchemy implementations.
5. App lifespan wires up the DB engine so `app.state` carries both Redis and engine.
6. All existing tests continue to pass; new focused tests cover the new models,
   repos, and bootstrap wiring.

## Out of scope
- Raw payload capture (P2, feature 017).
- Analysis module framework (P3, feature 018).
- Billing runtime logic or payments.
- Alembic migrations (migration-friendly design; actual migration tooling is deferred).
- Replacing the Redis chat-preferences path (existing call-sites continue to use Redis).

## Domain model additions

### `TelegramUser` (src/domain/user.py)
```
id:                UUID (PK)
telegram_user_id:  int  (unique, Telegram's own int64 user ID)
telegram_username: str | None
first_name:        str | None
last_name:         str | None
created_at:        datetime (UTC)
updated_at:        datetime (UTC)
```

## Persistence model additions

### `UserRow` (table: `users`)
Mirrors `TelegramUser`.  `telegram_user_id` has a UNIQUE constraint.

### `ChatSettingsRow` (table: `chat_settings`)
```
chat_id:    BigInteger (PK — Telegram chat ID)
language:   String(8) NOT NULL DEFAULT 'ru'
created_at: DateTime (UTC)
updated_at: DateTime (UTC)
```
`chat_id` is the natural key; no surrogate UUID is needed.

## Infrastructure (src/storage/db.py)
- `make_engine(database_url, **kwargs) -> AsyncEngine`
  Converts `postgresql://` → `postgresql+asyncpg://` before creating the engine.
- `make_session_factory(engine) -> async_sessionmaker[AsyncSession]`
- `create_tables(engine) -> None`
  Issues `Base.metadata.create_all` inside an async transaction.
  Idempotent; safe to call on startup.

## Repository contracts

### UserRepository (Protocol)
```
save(user: TelegramUser) -> None          # upsert
get_by_id(id: UUID) -> TelegramUser | None
get_by_telegram_id(tg_id: int) -> TelegramUser | None
```

### ChatSettingsRepository (Protocol)
```
save(chat_id: int, settings: ChatSettings) -> None   # upsert
get(chat_id: int) -> ChatSettings | None
```

## Backward compatibility
- Redis-backed `get_chat_settings` / `save_chat_settings` are untouched.
- `ListingRepository` and `AnalysisJobRepository` protocols are unchanged.
- No existing call-site is modified.

## Validation
- Structural tests for `UserRow` and `ChatSettingsRow` (metadata inspection,
  no DB connection required).
- Integration-style tests for concrete repos using an in-memory SQLite engine
  (`sqlite+aiosqlite:///:memory:`) to avoid a PostgreSQL dependency in CI.
- Bootstrap test: app lifespan sets `app.state.engine`.
