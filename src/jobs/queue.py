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
# For Telegram jobs keyed on (chat_id, message_id); for other channels keyed
# on job.id.  The TTL is generous enough to outlast any realistic retry window
# without persisting keys indefinitely.
_IDEMPOTENCY_KEY_PREFIX = "flatscanner:enqueued"
_IDEMPOTENCY_TTL_SECONDS = 86_400  # 24 hours

# Lua script: atomically SET NX EX the idempotency key and LPUSH to the queue
# in a single round-trip.  Redis executes Lua scripts atomically — no other
# command can run between the SET and the LPUSH, which eliminates the partial-
# failure window where the key is set but the push never happens.
#
# KEYS[1] = idempotency key, KEYS[2] = queue key
# ARGV[1] = TTL (seconds, string), ARGV[2] = serialised job JSON
# Returns 1 if enqueued, 0 if the key already existed (duplicate).
_ENQUEUE_SCRIPT = """
local placed = redis.call('SET', KEYS[1], '1', 'NX', 'EX', ARGV[1])
if placed then
    redis.call('LPUSH', KEYS[2], ARGV[2])
    return 1
end
return 0
"""


async def dequeue_analysis_job(
    redis: Redis, *, timeout: int = 0
) -> AnalysisJob | None:
    """Block until a job is available on the queue and return it.

    Parameters
    ----------
    redis:
        Async Redis client.
    timeout:
        BRPOP timeout in seconds.  ``0`` blocks indefinitely until a job
        arrives.  A positive value returns ``None`` when the timeout elapses
        with no job available.

    Returns
    -------
    AnalysisJob | None
        The next job, or ``None`` if the BRPOP timed out.
    """
    result = await redis.brpop(QUEUE_KEY, timeout=timeout)
    if result is None:
        return None
    _, payload = result
    return AnalysisJob.model_validate_json(payload)


async def requeue_raw_payload(redis: Redis, payload: bytes | str) -> None:
    """Push a raw job payload back onto the queue for retry.

    Bypasses the idempotency check — used only to restore a job that was
    already dequeued and whose processing failed with a retryable error.
    The payload is pushed to the same side as normal enqueues (LPUSH) so
    the job is processed after any jobs already waiting in the queue.
    """
    await redis.lpush(QUEUE_KEY, payload)


async def enqueue_analysis_job(redis: Redis, job: AnalysisJob) -> bool:
    """Serialise *job* to JSON and push it onto the analysis job queue.

    Returns ``True`` if the job was enqueued, ``False`` if it was skipped
    because an identical request (same Telegram chat/message identity) has
    already been enqueued.

    Both the idempotency check and the queue push are executed inside a single
    Lua script so the operation is atomic: a transient Redis failure can never
    leave the key set without the corresponding LPUSH having succeeded.
    """
    tg_ctx = job.telegram_context
    if tg_ctx is not None:
        idempotency_key = f"{_IDEMPOTENCY_KEY_PREFIX}:{tg_ctx.chat_id}:{tg_ctx.message_id}"
    else:
        idempotency_key = f"{_IDEMPOTENCY_KEY_PREFIX}:{job.id}"
    result = await redis.eval(
        _ENQUEUE_SCRIPT,
        2,  # numkeys
        idempotency_key,
        QUEUE_KEY,
        str(_IDEMPOTENCY_TTL_SECONDS),
        job.model_dump_json(),
    )
    return bool(result)
