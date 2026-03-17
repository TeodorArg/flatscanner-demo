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

# Idempotency key namespace and TTL for deduplicating Telegram retries.
# Keyed on (chat_id, message_id) — the stable identity Telegram assigns to
# every user message.  The TTL is generous enough to outlast any realistic
# retry window without persisting keys indefinitely.
_IDEMPOTENCY_KEY_PREFIX = "flatscanner:enqueued"
_IDEMPOTENCY_TTL_SECONDS = 86_400  # 24 hours


async def enqueue_analysis_job(redis: Redis, job: AnalysisJob) -> bool:
    """Serialise *job* to JSON and push it onto the analysis job queue.

    Returns ``True`` if the job was enqueued, ``False`` if it was skipped
    because an identical request (same Telegram chat/message identity) has
    already been enqueued.  The idempotency key is set atomically with
    ``SET NX EX`` so concurrent retries from Telegram cannot slip through.
    """
    idempotency_key = (
        f"{_IDEMPOTENCY_KEY_PREFIX}:{job.telegram_chat_id}:{job.telegram_message_id}"
    )
    placed = await redis.set(idempotency_key, "1", nx=True, ex=_IDEMPOTENCY_TTL_SECONDS)
    if not placed:
        return False
    await redis.lpush(QUEUE_KEY, job.model_dump_json())
    return True
