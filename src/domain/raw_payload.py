"""Domain model for a captured raw adapter payload."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RawPayload(BaseModel):
    """Captured raw response from a listing provider adapter.

    One ``RawPayload`` row is written per adapter fetch, before any
    normalisation.  This allows the normalisation step to be replayed from
    the stored payload without re-fetching from the provider.

    Fields
    ------
    id:
        Surrogate UUID primary key.
    provider:
        Provider identifier string (e.g. ``"airbnb"``).
    source_url:
        The original listing URL submitted by the user.
    source_id:
        Provider-specific listing ID extracted from the raw payload, when
        available.  May be ``None`` if the payload does not include a
        recognisable ID field.
    payload:
        The unmodified dict returned by the provider adapter (e.g. the first
        item from the Apify actor dataset).
    captured_at:
        UTC timestamp at which the raw payload was captured.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    provider: str
    source_url: str
    source_id: str | None = None
    payload: dict[str, Any]
    captured_at: datetime = Field(default_factory=_utcnow)
