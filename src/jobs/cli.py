"""Container-friendly worker entrypoint."""

from __future__ import annotations

import asyncio
import logging

from redis.asyncio import Redis

from src.app.config import Settings
from src.jobs.worker import run_worker
from src.storage.db import make_engine, make_session_factory


async def run_worker_process(
    *,
    settings: Settings | None = None,
    redis: Redis | None = None,
) -> None:
    """Create the default runtime dependencies and start the queue worker.

    A single DB engine and session factory are created here and shared across
    all jobs; they are disposed on exit.  This avoids per-job engine churn
    while keeping session lifecycles short (one session per job, opened and
    closed inside the worker loop).
    """
    runtime_settings = settings or Settings()
    runtime_redis = redis or Redis.from_url(
        runtime_settings.redis_url,
        decode_responses=True,
    )
    created_redis = redis is None

    engine = make_engine(runtime_settings.database_url)
    session_factory = make_session_factory(engine)

    try:
        await run_worker(runtime_redis, runtime_settings, session_factory=session_factory)
    finally:
        if created_redis:
            await runtime_redis.aclose()
        await engine.dispose()


def main() -> None:
    """Start the worker process with production-friendly logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(run_worker_process())


if __name__ == "__main__":
    main()
