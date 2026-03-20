from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.app.config import Settings
from src.jobs.cli import run_worker_process


def _make_settings(**overrides) -> Settings:
    defaults = {
        "app_env": "testing",
        "telegram_bot_token": "test-token",
        "openrouter_api_key": "test-openrouter",
        "apify_api_token": "test-apify",
        "geoapify_api_key": "test-geoapify",
        "redis_url": "redis://localhost:6379/9",
    }
    defaults.update(overrides)
    return Settings(**defaults)


class TestRunWorkerProcess:
    @pytest.mark.asyncio
    async def test_uses_injected_redis_without_closing_it(self):
        settings = _make_settings()
        redis = AsyncMock()
        mock_engine = AsyncMock()
        mock_sf = MagicMock()

        with (
            patch("src.jobs.cli.make_engine", return_value=mock_engine),
            patch("src.jobs.cli.make_session_factory", return_value=mock_sf),
            patch("src.jobs.cli.run_worker", new_callable=AsyncMock) as mock_run,
        ):
            await run_worker_process(settings=settings, redis=redis)

        mock_run.assert_awaited_once_with(redis, settings, session_factory=mock_sf)
        redis.aclose.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_creates_and_closes_redis_from_settings(self):
        settings = _make_settings(redis_url="redis://redis:6379/0")
        redis = AsyncMock()
        mock_engine = AsyncMock()

        with (
            patch("src.jobs.cli.Redis.from_url", return_value=redis) as mock_from_url,
            patch("src.jobs.cli.make_engine", return_value=mock_engine),
            patch("src.jobs.cli.make_session_factory", return_value=MagicMock()),
            patch("src.jobs.cli.run_worker", new_callable=AsyncMock) as mock_run,
        ):
            await run_worker_process(settings=settings)

        mock_from_url.assert_called_once_with("redis://redis:6379/0", decode_responses=True)
        assert mock_run.await_count == 1
        redis.aclose.assert_awaited_once()
