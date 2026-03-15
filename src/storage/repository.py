"""Abstract repository interfaces for the storage layer.

Concrete implementations will use an async SQLAlchemy session.  The
protocol approach keeps the domain and analysis code decoupled from the
database driver so that unit tests can use in-memory substitutes.
"""

from __future__ import annotations

import uuid
from typing import Protocol

from src.domain.listing import AnalysisJob, NormalizedListing


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
