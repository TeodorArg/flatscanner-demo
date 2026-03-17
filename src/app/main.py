from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from redis.asyncio import Redis

from src.app.config import Settings
from src.telegram.router import router as telegram_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    app.state.redis = redis
    try:
        yield
    finally:
        await redis.aclose()


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = Settings()

    app = FastAPI(
        title="flatscanner",
        description="Rental listing analysis service",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.state.settings = settings
    # Default to None; overwritten by lifespan on startup.
    app.state.redis = None

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "ok"}

    app.include_router(telegram_router)

    return app


# Module-level app instance used by uvicorn and import-based runners
app = create_app()
