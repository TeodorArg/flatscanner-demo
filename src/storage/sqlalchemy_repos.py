"""Concrete SQLAlchemy async repository implementations.

These classes satisfy the ``UserRepository`` and ``ChatSettingsRepository``
protocols defined in ``repository.py``.  Each instance is bound to a single
``AsyncSession`` and must not outlive its session's lifecycle.

Usage::

    async with session_factory() as session:
        users = SQLAlchemyUserRepository(session)
        user = await users.get_by_telegram_id(12345)
        if user is None:
            user = TelegramUser(telegram_user_id=12345, first_name="Alice")
            await users.save(user)
        await session.commit()
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.user import TelegramUser
from src.i18n.types import Language
from src.storage.chat_settings import ChatSettings
from src.storage.models import ChatSettingsRow, UserRow


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------


def _user_to_row(user: TelegramUser) -> UserRow:
    return UserRow(
        id=user.id,
        telegram_user_id=user.telegram_user_id,
        telegram_username=user.telegram_username,
        first_name=user.first_name,
        last_name=user.last_name,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _row_to_user(row: UserRow) -> TelegramUser:
    return TelegramUser(
        id=row.id,
        telegram_user_id=row.telegram_user_id,
        telegram_username=row.telegram_username,
        first_name=row.first_name,
        last_name=row.last_name,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _row_to_settings(row: ChatSettingsRow) -> ChatSettings:
    try:
        language = Language(row.language)
    except ValueError:
        from src.i18n.types import DEFAULT_LANGUAGE

        language = DEFAULT_LANGUAGE
    return ChatSettings(language=language)


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------


class SQLAlchemyUserRepository:
    """SQLAlchemy-backed implementation of ``UserRepository``."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: TelegramUser) -> None:
        """Upsert *user* into the ``users`` table.

        ``telegram_user_id`` is the natural key for Telegram identities.  When
        a row for this Telegram user already exists we update it in-place so
        that the stable ``id`` (UUID) and ``created_at`` are preserved and the
        caller does not need to hold onto the original UUID.  If no row exists
        yet, ``session.merge()`` performs the initial INSERT using the UUID
        carried by *user*.
        """
        stmt = sa.select(UserRow).where(UserRow.telegram_user_id == user.telegram_user_id)
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.telegram_username = user.telegram_username
            existing.first_name = user.first_name
            existing.last_name = user.last_name
            existing.updated_at = _utcnow()
        else:
            row = _user_to_row(user)
            await self._session.merge(row)

    async def get_by_id(self, user_id: uuid.UUID) -> TelegramUser | None:
        """Return the user with the given UUID primary key, or ``None``."""
        row = await self._session.get(UserRow, user_id)
        return _row_to_user(row) if row is not None else None

    async def get_by_telegram_id(self, telegram_user_id: int) -> TelegramUser | None:
        """Return a user by their Telegram int64 user ID, or ``None``."""
        stmt = sa.select(UserRow).where(UserRow.telegram_user_id == telegram_user_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _row_to_user(row) if row is not None else None


class SQLAlchemyChatSettingsRepository:
    """SQLAlchemy-backed implementation of ``ChatSettingsRepository``."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, chat_id: int, settings: ChatSettings) -> None:
        """Upsert settings for *chat_id*.

        If a row for *chat_id* already exists ``updated_at`` is refreshed;
        otherwise a new row is inserted.
        """
        existing = await self._session.get(ChatSettingsRow, chat_id)
        if existing is None:
            row = ChatSettingsRow(
                chat_id=chat_id,
                language=settings.language.value,
            )
            self._session.add(row)
        else:
            existing.language = settings.language.value
            existing.updated_at = _utcnow()

    async def get(self, chat_id: int) -> ChatSettings | None:
        """Return persisted settings for *chat_id*, or ``None`` if absent."""
        row = await self._session.get(ChatSettingsRow, chat_id)
        return _row_to_settings(row) if row is not None else None
