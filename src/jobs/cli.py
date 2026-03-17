"""Container-friendly worker entrypoint."""

from __future__ import annotations

import asyncio
import logging

from redis.asyncio import Redis

from src.app.config import Settings
from src.jobs.worker import run_worker


async def run_worker_process(
    *,
    settings: Settings | None = None,
    redis: Redis | None = None,
) -> None:
    """Create the default runtime dependencies and start the queue worker."""
    runtime_settings = settings or Settings()
    runtime_redis = redis or Redis.from_url(
        runtime_settings.redis_url,
        decode_responses=True,
    )
    created_redis = redis is None

    try:
        await run_worker(runtime_redis, runtime_settings)
    finally:
        if created_redis:
            await runtime_redis.aclose()


def main() -> None:
    """Start the worker process with production-friendly logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(run_worker_process())


if __name__ == "__main__":
    main()

