"""Web-channel read models (request/response schemas).

These Pydantic models define the HTTP contract for the web delivery channel.
They are intentionally channel-neutral in spirit: they carry only the fields
needed by a browser or API consumer and never reference Telegram internals.

S4 status: shapes are defined and validated; persistence-backed status and
result retrieval are deferred to a later slice.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Submit
# ---------------------------------------------------------------------------


class WebSubmitRequest(BaseModel):
    """Request body for POST /web/submit."""

    url: str = Field(description="Listing URL to analyse.")
    language: str = Field(
        default="en",
        description="BCP-47 language tag for the result (e.g. 'en', 'ru').",
    )
    correlation_id: str | None = Field(
        default=None,
        description="Optional caller-supplied identifier for tracking the request.",
    )


class WebSubmitResponse(BaseModel):
    """Response body for POST /web/submit."""

    job_id: str = Field(description="UUID of the enqueued analysis job.")
    status: str = Field(description="Initial job status; always 'queued' on success.")
    queued_at: datetime = Field(
        default_factory=_utcnow,
        description="UTC timestamp when the job was accepted.",
    )


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


class WebJobStatusResponse(BaseModel):
    """Response body for GET /web/status/{job_id}."""

    job_id: str
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


class WebPriceInfo(BaseModel):
    """Compact price representation for web consumers."""

    verdict: str
    explanation: str


class WebAnalysisResultResponse(BaseModel):
    """Response body for GET /web/result/{job_id}.

    Mirrors ``AnalysisResult`` but uses plain Python types so the response
    is easy to consume from any HTTP client without needing domain imports.
    """

    job_id: str
    status: str
    display_title: str = ""
    summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    price: WebPriceInfo | None = None
    # ``None`` means the result is not yet available (job still running or
    # the result backend is not yet wired up).
    result_available: bool = False
