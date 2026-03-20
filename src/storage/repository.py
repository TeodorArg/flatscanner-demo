"""Abstract repository interfaces for the storage layer.

Concrete implementations will use an async SQLAlchemy session.  The
protocol approach keeps the domain and analysis code decoupled from the
database driver so that unit tests can use in-memory substitutes.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from src.domain.listing import AnalysisJob, NormalizedListing
from src.domain.user import TelegramUser
from src.storage.chat_settings import ChatSettings


class ListingRepository(Protocol):
    """Read/write access to persisted ``NormalizedListing`` records."""

    async def save(self, listing: NormalizedListing) -> None:
        """Persist a new or updated listing."""
        ...

    async def get_by_id(self, listing_id: uuid.UUID) -> NormalizedListing | None:
        """Return the listing with the given primary key, or ``None``."""
        ...

    async def get_by_source(
        self, provider: str, source_id: str
    ) -> NormalizedListing | None:
        """Return a listing by its provider and provider-specific ID, or ``None``."""
        ...


class AnalysisJobRepository(Protocol):
    """Read/write access to persisted ``AnalysisJob`` records."""

    async def save(self, job: AnalysisJob) -> None:
        """Persist a new or updated job."""
        ...

    async def get_by_id(self, job_id: uuid.UUID) -> AnalysisJob | None:
        """Return the job with the given primary key, or ``None``."""
        ...


class UserRepository(Protocol):
    """Read/write access to persisted ``TelegramUser`` records."""

    async def save(self, user: TelegramUser) -> None:
        """Upsert a user by the ``telegram_user_id`` natural key.

        If a row with the same ``telegram_user_id`` already exists, its
        mutable fields (username, first_name, last_name, updated_at) are
        updated while the stable UUID ``id`` and ``created_at`` are
        preserved.  If no such row exists, a new row is inserted.
        """
        ...

    async def get_by_id(self, user_id: uuid.UUID) -> TelegramUser | None:
        """Return the user with the given primary key, or ``None``."""
        ...

    async def get_by_telegram_id(self, telegram_user_id: int) -> TelegramUser | None:
        """Return a user by their Telegram int64 user ID, or ``None``."""
        ...


class ChatSettingsRepository(Protocol):
    """Read/write access to persisted per-chat bot settings."""

    async def save(self, chat_id: int, settings: ChatSettings) -> None:
        """Persist settings for *chat_id* (upsert)."""
        ...

    async def get(self, chat_id: int) -> ChatSettings | None:
        """Return persisted settings for *chat_id*, or ``None`` if absent."""
        ...
