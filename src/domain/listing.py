"""Normalized listing domain models and related enumerations.

These Pydantic models represent the shared, provider-agnostic view of a
rental listing.  Raw provider payloads (e.g. Airbnb JSON from Apify) are
mapped into these models before the enrichment and analysis stages.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field

from src.i18n.types import DEFAULT_LANGUAGE, Language


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ListingProvider(str, Enum):
    """Supported listing source platforms."""

    AIRBNB = "airbnb"
    UNKNOWN = "unknown"


class JobStatus(str, Enum):
    """Lifecycle states for an analysis job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


class ListingLocation(BaseModel):
    """Geographic and address information for a listing."""

    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None
    neighbourhood: str | None = None


class PriceInfo(BaseModel):
    """Pricing details extracted from a listing."""

    amount: Decimal
    currency: str
    # Billing period as reported by the provider, e.g. "night", "week", "month"
    period: str = "night"
    cleaning_fee: Decimal | None = None
    service_fee: Decimal | None = None


# ---------------------------------------------------------------------------
# Core domain models
# ---------------------------------------------------------------------------


class NormalizedListing(BaseModel):
    """Provider-agnostic representation of a rental listing.

    Produced by the adapter layer after mapping a raw provider payload.
    Raw provider payloads are stored separately in the persistence layer;
    this model contains only normalized, provider-agnostic fields.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    provider: ListingProvider
    source_url: str
    # Provider-specific listing identifier (e.g. Airbnb room ID)
    source_id: str

    title: str
    description: str | None = None

    location: ListingLocation = Field(default_factory=ListingLocation)
    price: PriceInfo | None = None

    bedrooms: int | None = None
    bathrooms: float | None = None
    max_guests: int | None = None
    amenities: list[str] = Field(default_factory=list)

    rating: float | None = None
    review_count: int | None = None

    host_name: str | None = None
    host_is_superhost: bool | None = None

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class AnalysisJob(BaseModel):
    """Tracks the state of a single listing analysis request.

    Created when a Telegram user submits a listing URL.  The job record
    links the original request (chat/message IDs) to the resulting
    ``NormalizedListing`` and, eventually, the analysis result.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source_url: str
    provider: ListingProvider

    status: JobStatus = JobStatus.PENDING
    # Set once the raw payload has been normalized
    listing_id: uuid.UUID | None = None

    telegram_chat_id: int
    telegram_message_id: int
    # Set by the webhook handler after sending the initial progress message so
    # the worker can edit / delete it during processing.
    telegram_progress_message_id: int | None = None

    # Language snapshotted at enqueue time so in-flight jobs are stable even
    # if the chat preference changes before the job completes.
    language: Language = DEFAULT_LANGUAGE

    error_message: str | None = None

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
