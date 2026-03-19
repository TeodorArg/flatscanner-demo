"""SQLAlchemy ORM persistence models for the flatscanner storage layer.

These models define the database schema.  They are intentionally kept
separate from the Pydantic domain models in ``src/domain/`` so that
serialization concerns (Pydantic) and persistence concerns (SQLAlchemy)
remain independent.

Relationships between the two layers:
  - ``ListingRow``  ↔  ``NormalizedListing``
  - ``AnalysisJobRow`` ↔  ``AnalysisJob``
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class ListingRow(Base):
    """Persisted form of a ``NormalizedListing``.

    The ``raw_payload`` JSON column stores the original provider response so
    that normalisation can be re-run without re-fetching from Apify.
    """

    __tablename__ = "listings"
    __table_args__ = (
        UniqueConstraint("provider", "source_id", name="uq_listings_provider_source_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[str] = mapped_column(String(256), nullable=False)

    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Location
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(256), nullable=True)
    country: Mapped[str | None] = mapped_column(String(256), nullable=True)
    neighbourhood: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Pricing
    price_amount: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    price_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    price_period: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cleaning_fee: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    service_fee: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)

    # Property details
    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bathrooms: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_guests: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Stored as a JSON array of strings
    amenities: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Ratings and reviews
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Host
    host_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    host_is_superhost: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )


class AnalysisJobRow(Base):
    """Persisted form of an ``AnalysisJob``.

    Links a Telegram request to its processing state and, once normalisation
    completes, to the resulting ``ListingRow``.
    """

    __tablename__ = "analysis_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")

    listing_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("listings.id", ondelete="SET NULL"),
        nullable=True,
    )

    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    telegram_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Language snapshotted at enqueue time; defaults to Russian.
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="ru")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )


class TelegramChatPreferenceRow(Base):
    """Persisted language preference for a Telegram chat.

    Keyed by ``chat_id`` (Telegram's stable numeric identifier).  A row is
    created the first time a chat explicitly sets a language; chats without a
    row default to Russian at runtime.
    """

    __tablename__ = "telegram_chat_preferences"

    chat_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    language: Mapped[str] = mapped_column(
        String(8), nullable=False, default="ru"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )
