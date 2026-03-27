"""FastAPI router for the web delivery channel.

Exposes three endpoint shapes for S4:

- ``POST /web/submit``   — placeholder; returns 501 until S5 wires up real
                           WEB-channel enqueuing.
- ``GET  /web/status/{job_id}`` — return the current job status (S4: stub,
                                   persistence not yet wired up).
- ``GET  /web/result/{job_id}`` — return the analysis result (S4: stub,
                                   result storage not yet wired up).

No authentication, billing, or caching is implemented in this slice.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from src.web.models import (
    WebAnalysisResultResponse,
    WebJobStatusResponse,
    WebSubmitRequest,
)

router = APIRouter(prefix="/web", tags=["web"])


@router.post("/submit", status_code=501)
async def submit(body: WebSubmitRequest) -> dict:
    """Submit a listing URL for analysis via the web channel.

    S4 placeholder: web job submission is not yet wired up.  Returns 501
    Not Implemented until S5 connects real enqueuing for the WEB channel.
    The request body is validated so the contract shape is exercised, but
    no job is created or enqueued.
    """
    raise HTTPException(
        status_code=501,
        detail=(
            "Web job submission is not yet implemented. "
            "Enqueuing for the WEB channel is deferred to S5."
        ),
    )


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
