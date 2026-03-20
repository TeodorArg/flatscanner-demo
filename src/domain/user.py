"""Telegram-linked user identity domain model.

This module defines the provider-agnostic user record used throughout the
application.  The ``TelegramUser`` model is produced when a Telegram update
is first received from an unknown user and persisted via ``UserRepository``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TelegramUser(BaseModel):
    """Represents a user who has interacted with the bot via Telegram.

    ``telegram_user_id`` is Telegram's own stable integer identifier for the
    user.  ``id`` is the application-internal UUID primary key.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)

    # Telegram's own int64 user identifier — unique and stable across chats.
    telegram_user_id: int

    telegram_username: str | None = None
    first_name: str | None = None
    last_name: str | None = None

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
