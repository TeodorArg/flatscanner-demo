"""Background worker loop for analysis jobs.

Provides two entry points:

- ``process_once`` — dequeue one job and process it.  Returns ``True`` if a
  job was processed, ``False`` if the queue was empty (BRPOP timeout).
  Designed for easy testing and one-shot execution.

- ``run_worker`` — continuously dequeue and process jobs until cancelled.
  Requeues jobs on retryable failures so transient adapter/OpenRouter/
  Telegram errors do not cause silent job loss.  ``UnsupportedProviderError``
  is treated as non-retryable: the job is logged and dropped.

No heavyweight worker framework is introduced here; the open library choice
(documented in docs/project/backend/backend-docs.md) remains deferred.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from pydantic import ValidationError

from src.domain.listing import AnalysisJob
from src.jobs.processor import UnsupportedProviderError, process_job
from src.jobs.queue import QUEUE_KEY, dequeue_analysis_job, requeue_raw_payload

if TYPE_CHECKING:
    from redis.asyncio import Redis

    from src.app.config import Settings

logger = logging.getLogger(__name__)


async def process_once(redis: "Redis", settings: "Settings") -> bool:
    """Dequeue and process one job with a non-blocking timeout.

    Parameters
    ----------
    redis:
        Async Redis client connected to the queue.
    settings:
        Application settings forwarded to ``process_job``.

    Returns
    -------
    bool
        ``True`` if a job was dequeued and processing was attempted,
        ``False`` if the queue was empty when the 1-second BRPOP timeout
        elapsed.

    Notes
    -----
    Processing errors are **not** swallowed here — the caller decides
    whether to retry, dead-letter, or log and continue.
    """
    job = await dequeue_analysis_job(redis, timeout=1)
    if job is None:
        return False
    await process_job(job, settings)
    return True


async def run_worker(redis: "Redis", settings: "Settings") -> None:
    """Continuously dequeue and process analysis jobs until cancelled.

    Each iteration blocks for up to 1 second waiting for a job.  The raw
    Redis payload is captured before processing so that any retryable
    failure can restore the job to the queue:

    - ``UnsupportedProviderError`` — non-retryable; job is logged and
      dropped.
    - Any other exception — job is requeued via ``requeue_raw_payload``
      before the loop continues, preventing silent job loss.

    The loop exits cleanly when ``asyncio.CancelledError`` is raised (e.g.
    from an OS signal or test cancellation).
    """
    logger.info("Worker started — waiting for jobs on queue")
    while True:
        raw_payload: bytes | None = None
        try:
            result = await redis.brpop(QUEUE_KEY, timeout=1)
            if result is None:
                continue
            _, raw_payload = result
            job = AnalysisJob.model_validate_json(raw_payload)
            await process_job(job, settings)
        except asyncio.CancelledError:
            logger.info("Worker cancelled — shutting down")
            break
        except UnsupportedProviderError as exc:
            logger.error("Unsupported provider, dropping job: %s", exc)
        except ValidationError as exc:
            logger.error(
                "Malformed job payload — dropping (not retryable): %s", exc
            )
        except Exception as exc:
            logger.exception("Unexpected error processing job: %s", exc)
            if raw_payload is not None:
                try:
                    await requeue_raw_payload(redis, raw_payload)
                except Exception as requeue_exc:
                    logger.error(
                        "Failed to requeue job payload after processing error"
                        " — job may be lost: %s",
                        requeue_exc,
                    )
