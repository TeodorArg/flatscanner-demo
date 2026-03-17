"""Background worker loop for analysis jobs.

Provides two entry points:

- ``process_once`` — dequeue one job and process it.  Returns ``True`` if a
  job was processed, ``False`` if the queue was empty (BRPOP timeout).
  Designed for easy testing and one-shot execution.

- ``run_worker`` — continuously dequeue and process jobs until cancelled.
  Logs errors and continues on transient failures so the worker stays alive
  across individual job failures.

No heavyweight worker framework is introduced here; the open library choice
(documented in docs/project/backend/backend-docs.md) remains deferred.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from src.jobs.processor import UnsupportedProviderError, process_job
from src.jobs.queue import dequeue_analysis_job

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

    Each iteration blocks for up to 1 second waiting for a job.  On
    ``UnsupportedProviderError`` or other processing exceptions the error is
    logged and the loop continues, preventing a single bad job from killing
    the worker.

    The loop exits cleanly when ``asyncio.CancelledError`` is raised (e.g.
    from an OS signal or test cancellation).
    """
    logger.info("Worker started — waiting for jobs on queue")
    while True:
        try:
            await process_once(redis, settings)
        except asyncio.CancelledError:
            logger.info("Worker cancelled — shutting down")
            break
        except UnsupportedProviderError as exc:
            logger.error("Unsupported provider, skipping job: %s", exc)
        except Exception as exc:
            logger.exception("Unexpected error processing job: %s", exc)
