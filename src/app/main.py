from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from src.app.config import Settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: nothing to connect on bootstrap; services added in later slices
    yield
    # Shutdown: teardown added alongside each service


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

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "ok"}

    return app


# Module-level app instance used by uvicorn and import-based runners
app = create_app()
