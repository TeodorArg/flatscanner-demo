"""Integration-style tests for the concrete SQLAlchemy repositories.

Tests run against an in-memory SQLite database via the ``aiosqlite`` driver
so that no PostgreSQL instance is required in CI.  The SQLite backend has
minor type differences (e.g. UUIDs stored as TEXT, no native timezone) but
is sufficient to verify correct INSERT/SELECT/upsert behaviour.
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.domain.user import TelegramUser
from src.i18n.types import Language
from src.storage.chat_settings import ChatSettings
from src.storage.db import create_tables, make_engine, make_session_factory
from src.storage.sqlalchemy_repos import (
    SQLAlchemyChatSettingsRepository,
    SQLAlchemyUserRepository,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def engine() -> AsyncEngine:  # type: ignore[override]
    eng = make_engine("sqlite+aiosqlite:///:memory:")
    await create_tables(eng)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncSession:  # type: ignore[override]
    factory: async_sessionmaker[AsyncSession] = make_session_factory(engine)
    async with factory() as s:
        yield s


# ---------------------------------------------------------------------------
# make_engine / _async_database_url
# ---------------------------------------------------------------------------


class TestMakeEngine:
    def test_postgresql_url_is_converted(self):
        from src.storage.db import _async_database_url

        result = _async_database_url("postgresql://user:pass@localhost/db")
        assert result == "postgresql+asyncpg://user:pass@localhost/db"

    def test_postgres_alias_is_converted(self):
        from src.storage.db import _async_database_url

        result = _async_database_url("postgres://user:pass@localhost/db")
        assert result == "postgresql+asyncpg://user:pass@localhost/db"

    def test_already_asyncpg_url_unchanged(self):
        from src.storage.db import _async_database_url

        url = "postgresql+asyncpg://user:pass@localhost/db"
        assert _async_database_url(url) == url

    def test_sqlite_url_unchanged(self):
        from src.storage.db import _async_database_url

        url = "sqlite+aiosqlite:///:memory:"
        assert _async_database_url(url) == url


# ---------------------------------------------------------------------------
# SQLAlchemyUserRepository
# ---------------------------------------------------------------------------


class TestSQLAlchemyUserRepository:
    async def test_save_and_get_by_id(self, session: AsyncSession):
        repo = SQLAlchemyUserRepository(session)
        user = TelegramUser(telegram_user_id=111, first_name="Alice")
        await repo.save(user)
        await session.commit()

        fetched = await repo.get_by_id(user.id)
        assert fetched is not None
        assert fetched.id == user.id
        assert fetched.telegram_user_id == 111
        assert fetched.first_name == "Alice"

    async def test_get_by_id_returns_none_for_unknown(self, session: AsyncSession):
        repo = SQLAlchemyUserRepository(session)
        result = await repo.get_by_id(uuid.uuid4())
        assert result is None

    async def test_save_and_get_by_telegram_id(self, session: AsyncSession):
        repo = SQLAlchemyUserRepository(session)
        user = TelegramUser(telegram_user_id=222, telegram_username="bob")
        await repo.save(user)
        await session.commit()

        fetched = await repo.get_by_telegram_id(222)
        assert fetched is not None
        assert fetched.telegram_username == "bob"

    async def test_get_by_telegram_id_returns_none_for_unknown(self, session: AsyncSession):
        repo = SQLAlchemyUserRepository(session)
        result = await repo.get_by_telegram_id(999999)
        assert result is None

    async def test_save_updates_existing_user(self, session: AsyncSession):
        repo = SQLAlchemyUserRepository(session)
        user = TelegramUser(telegram_user_id=333, first_name="Carol")
        await repo.save(user)
        await session.commit()

        updated = user.model_copy(update={"first_name": "Caroline"})
        await repo.save(updated)
        await session.commit()

        fetched = await repo.get_by_id(user.id)
        assert fetched is not None
        assert fetched.first_name == "Caroline"

    async def test_optional_fields_can_be_none(self, session: AsyncSession):
        repo = SQLAlchemyUserRepository(session)
        user = TelegramUser(telegram_user_id=444)
        await repo.save(user)
        await session.commit()

        fetched = await repo.get_by_id(user.id)
        assert fetched is not None
        assert fetched.telegram_username is None
        assert fetched.first_name is None
        assert fetched.last_name is None

    async def test_save_with_different_uuid_same_telegram_id_does_not_raise(
        self, session: AsyncSession
    ):
        """Saving a fresh TelegramUser with the same telegram_user_id but a
        different UUID must not raise a UNIQUE constraint violation.  The
        original row identity (UUID, created_at) must be preserved."""
        repo = SQLAlchemyUserRepository(session)

        first = TelegramUser(telegram_user_id=555, first_name="First")
        await repo.save(first)
        await session.commit()
        original_id = first.id

        # Simulate a second message from the same Telegram user arriving with
        # a freshly-constructed domain model (new UUID, updated name).
        second = TelegramUser(telegram_user_id=555, first_name="Second")
        assert second.id != original_id  # sanity: different UUID

        await repo.save(second)  # must not raise
        await session.commit()

        # The row fetched by the *original* UUID still exists and is updated.
        fetched = await repo.get_by_id(original_id)
        assert fetched is not None
        assert fetched.telegram_user_id == 555
        assert fetched.first_name == "Second"

        # No duplicate rows — fetching by telegram_id returns the same row.
        by_tg = await repo.get_by_telegram_id(555)
        assert by_tg is not None
        assert by_tg.id == original_id


# ---------------------------------------------------------------------------
# SQLAlchemyChatSettingsRepository
# ---------------------------------------------------------------------------


class TestSQLAlchemyChatSettingsRepository:
    async def test_get_returns_none_when_absent(self, session: AsyncSession):
        repo = SQLAlchemyChatSettingsRepository(session)
        result = await repo.get(chat_id=1001)
        assert result is None

    async def test_save_and_get(self, session: AsyncSession):
        repo = SQLAlchemyChatSettingsRepository(session)
        settings = ChatSettings(language=Language.EN)
        await repo.save(chat_id=1001, settings=settings)
        await session.commit()

        fetched = await repo.get(chat_id=1001)
        assert fetched is not None
        assert fetched.language == Language.EN

    async def test_save_is_idempotent_for_same_chat(self, session: AsyncSession):
        repo = SQLAlchemyChatSettingsRepository(session)
        await repo.save(chat_id=2001, settings=ChatSettings(language=Language.RU))
        await session.commit()
        await repo.save(chat_id=2001, settings=ChatSettings(language=Language.EN))
        await session.commit()

        fetched = await repo.get(chat_id=2001)
        assert fetched is not None
        assert fetched.language == Language.EN

    async def test_different_chats_are_independent(self, session: AsyncSession):
        repo = SQLAlchemyChatSettingsRepository(session)
        await repo.save(chat_id=3001, settings=ChatSettings(language=Language.EN))
        await repo.save(chat_id=3002, settings=ChatSettings(language=Language.ES))
        await session.commit()

        assert (await repo.get(chat_id=3001)).language == Language.EN  # type: ignore[union-attr]
        assert (await repo.get(chat_id=3002)).language == Language.ES  # type: ignore[union-attr]

    async def test_default_language_is_ru_when_row_stored_with_default(
        self, session: AsyncSession
    ):
        repo = SQLAlchemyChatSettingsRepository(session)
        await repo.save(chat_id=4001, settings=ChatSettings())
        await session.commit()

        fetched = await repo.get(chat_id=4001)
        assert fetched is not None
        assert fetched.language == Language.RU
