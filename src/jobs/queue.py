"""Redis-backed analysis job queue.

Uses raw redis.asyncio primitives (LPUSH / BRPOP) so the worker library
choice remains open.  The queue key is ``flatscanner:analysis_jobs``.

Consumers dequeue with::

    payload = await redis.brpop(QUEUE_KEY, timeout=0)
    job = AnalysisJob.model_validate_json(payload[1])
"""

from redis.asyncio import Redis

from src.domain.listing import AnalysisJob

QUEUE_KEY = "flatscanner:analysis_jobs"


async def enqueue_analysis_job(redis: Redis, job: AnalysisJob) -> None:
    """Serialise *job* to JSON and push it onto the analysis job queue."""
    await redis.lpush(QUEUE_KEY, job.model_dump_json())
