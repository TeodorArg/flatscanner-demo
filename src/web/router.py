"""FastAPI router for the web delivery channel.

Exposes three endpoint shapes for S4:

- ``POST /web/submit``   — accept a listing URL, enqueue a WEB-channel job,
                           return the job UUID.
- ``GET  /web/status/{job_id}`` — return the current job status (S4: stub,
                                   persistence not yet wired up).
- ``GET  /web/result/{job_id}`` — return the analysis result (S4: stub,
                                   result storage not yet wired up).

No authentication, billing, or caching is implemented in this slice.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException, Request

from src.application.analysis import submit_analysis_request
from src.domain.delivery import DeliveryChannel, WebDeliveryContext
from src.domain.listing import AnalysisJob
from src.i18n.types import DEFAULT_LANGUAGE, Language
from src.web.models import (
    WebAnalysisResultResponse,
    WebJobStatusResponse,
    WebSubmitRequest,
    WebSubmitResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/web", tags=["web"])


@router.post("/submit", response_model=WebSubmitResponse, status_code=202)
async def submit(request: Request, body: WebSubmitRequest) -> WebSubmitResponse:
    """Submit a listing URL for analysis via the web channel.

    Enqueues a channel-neutral ``AnalysisJob`` with
    ``delivery_channel=WEB``.  The job is processed asynchronously; the
    caller receives a ``job_id`` that can be used to poll
    ``GET /web/status/{job_id}`` and ``GET /web/result/{job_id}``.

    Returns 202 Accepted on success.  Returns 422 if the language code is
    not recognised, or 502 if the job queue is unavailable.
    """
    # Resolve language — fall back to default on unknown codes.
    try:
        lang = Language(body.language)
    except ValueError:
        lang = DEFAULT_LANGUAGE

    # Detect provider from URL (best-effort; unknown URLs get UNKNOWN).
    from src.adapters.registry import detect_provider

    provider = detect_provider(body.url)

    job = AnalysisJob(
        source_url=body.url,
        provider=provider,
        delivery_channel=DeliveryChannel.WEB,
        web_context=WebDeliveryContext(correlation_id=body.correlation_id),
        language=lang,
    )

    redis = request.app.state.redis
    if redis is None:
        logger.warning("Redis unavailable; cannot enqueue web job for url=%s", body.url)
        raise HTTPException(status_code=502, detail="Queue unavailable; please retry")

    try:
        await submit_analysis_request(redis, job)
    except Exception as exc:
        logger.error("Failed to enqueue web job for url=%s: %s", body.url, exc)
        raise HTTPException(status_code=502, detail="Queue unavailable; please retry")

    return WebSubmitResponse(job_id=str(job.id), status="queued")


@router.get("/status/{job_id}", response_model=WebJobStatusResponse)
async def job_status(job_id: str) -> WebJobStatusResponse:
    """Return the current status of an analysis job.

    S4 stub: status persistence is not yet implemented.  Always returns
    ``{"status": "unknown"}`` with a note that tracking is deferred.
    """
    # Validate UUID format so callers get a clear 422 on bad input.
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="job_id must be a valid UUID")

    # Status persistence is deferred to a later slice.
    return WebJobStatusResponse(job_id=job_id, status="unknown")


@router.get("/result/{job_id}", response_model=WebAnalysisResultResponse)
async def job_result(job_id: str) -> WebAnalysisResultResponse:
    """Return the analysis result for a completed job.

    S4 stub: result storage is not yet implemented.  Always returns a
    response with ``result_available=False``.
    """
    try:
        uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="job_id must be a valid UUID")

    # Result storage is deferred to a later slice.
    return WebAnalysisResultResponse(job_id=job_id, status="unknown", result_available=False)
