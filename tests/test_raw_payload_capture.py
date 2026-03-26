"""Focused tests for P2 raw payload capture.

Covers:
- AdapterResult contract: adapter returns both raw dict and NormalizedListing
- AirbnbAdapter.fetch() conforms to AdapterResult contract
- processor.py persists raw payload when raw_payload_repo is provided
- processor.py skips persistence when raw_payload_repo is None
- processor.py swallows and logs save errors without blocking the pipeline
- process_once wires a DB-backed repo when session_factory is provided
- run_worker wires a DB-backed repo when session_factory is provided
- run_worker_process creates engine + session_factory once and passes them
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.adapters.airbnb import AirbnbAdapter
from src.adapters.apify_client import ApifyClient
from src.adapters.base import AdapterResult
from src.analysis.result import AnalysisResult, PriceVerdict
from src.analysis.service import AnalysisService
from src.domain.delivery import DeliveryChannel, TelegramDeliveryContext
from src.domain.listing import AnalysisJob, ListingProvider, NormalizedListing, PriceInfo
from src.domain.raw_payload import RawPayload
from src.i18n.types import Language
from src.jobs.processor import process_job


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_settings(**overrides):
    from src.app.config import Settings

    defaults = dict(
        app_env="testing",
        telegram_bot_token="test-bot-token",
        openrouter_api_key="test-key",
        apify_api_token="test-apify",
    )
    defaults.update(overrides)
    return Settings(**defaults)


def _make_job(**overrides) -> AnalysisJob:
    defaults = dict(
        source_url="https://www.airbnb.com/rooms/12345",
        provider=ListingProvider.AIRBNB,
        delivery_channel=DeliveryChannel.TELEGRAM,
        telegram_context=TelegramDeliveryContext(chat_id=1001, message_id=7),
    )
    defaults.update(overrides)
    return AnalysisJob(**defaults)


def _make_listing() -> NormalizedListing:
    return NormalizedListing(
        provider=ListingProvider.AIRBNB,
        source_url="https://www.airbnb.com/rooms/12345",
        source_id="12345",
        title="Cozy flat in Berlin",
        price=PriceInfo(amount=Decimal("80"), currency="EUR"),
    )


def _make_result() -> AnalysisResult:
    return AnalysisResult(
        display_title="Cozy flat in Berlin",
        summary="A pleasant flat in central Berlin.",
        strengths=["Central location"],
        risks=["Noisy street"],
        price_verdict=PriceVerdict.FAIR,
        price_explanation="Price is in line with comparable listings.",
    )


def _make_passthrough_ts():
    from src.translation.service import TranslationService

    ts = MagicMock(spec=TranslationService)
    ts.translate = AsyncMock(side_effect=lambda result, lang: result)
    return ts


def _airbnb_raw_payload(listing_id: str = "12345") -> dict:
    return {
        "id": listing_id,
        "name": "Cozy flat in Berlin",
        "lat": 52.5,
        "lng": 13.4,
    }


# ---------------------------------------------------------------------------
# AdapterResult dataclass
# ---------------------------------------------------------------------------


class TestAdapterResult:
    def test_has_raw_and_listing_fields(self):
        listing = _make_listing()
        raw = {"id": "12345", "name": "Cozy flat"}
        result = AdapterResult(raw=raw, listing=listing)

        assert result.raw is raw
        assert result.listing is listing

    def test_raw_is_dict(self):
        listing = _make_listing()
        result = AdapterResult(raw={"key": "value"}, listing=listing)
        assert isinstance(result.raw, dict)


# ---------------------------------------------------------------------------
# AirbnbAdapter.fetch() returns AdapterResult
# ---------------------------------------------------------------------------


class TestAirbnbAdapterFetchContract:
    _URL = "https://www.airbnb.com/rooms/12345"

    def _adapter(self) -> AirbnbAdapter:
        from src.app.config import Settings

        settings = Settings(
            app_env="testing",
            apify_api_token="test-token",
            apify_airbnb_actor_id="test~actor",
        )
        return AirbnbAdapter(settings=settings)

    @pytest.mark.asyncio
    async def test_fetch_returns_adapter_result_instance(self):
        payload = _airbnb_raw_payload()
        adapter = self._adapter()

        with patch.object(ApifyClient, "run_and_get_items", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = [payload]
            result = await adapter.fetch(self._URL)

        assert isinstance(result, AdapterResult)

    @pytest.mark.asyncio
    async def test_fetch_raw_is_the_unmodified_actor_item(self):
        payload = _airbnb_raw_payload("99999")
        adapter = self._adapter()

        with patch.object(ApifyClient, "run_and_get_items", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = [payload]
            result = await adapter.fetch(self._URL)

        assert result.raw is payload  # same object, not a copy

    @pytest.mark.asyncio
    async def test_fetch_listing_is_normalized_from_raw(self):
        payload = _airbnb_raw_payload("99999")
        adapter = self._adapter()

        with patch.object(ApifyClient, "run_and_get_items", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = [payload]
            result = await adapter.fetch(self._URL)

        assert result.listing.source_id == "99999"
        assert result.listing.provider == ListingProvider.AIRBNB


# ---------------------------------------------------------------------------
# processor.py raw payload wiring
# ---------------------------------------------------------------------------


class TestProcessorRawPayloadPersistence:
    @pytest.mark.asyncio
    async def test_raw_payload_saved_when_repo_provided(self):
        """process_job calls raw_payload_repo.save() when the repo is provided."""
        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        adapter_result = AdapterResult(raw={"id": "12345", "name": "Cozy flat"}, listing=listing)
        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=adapter_result)

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        mock_repo = AsyncMock()

        with patch("src.jobs.processor.send_message", new_callable=AsyncMock):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
                raw_payload_repo=mock_repo,
            )

        mock_repo.save.assert_awaited_once()
        saved: RawPayload = mock_repo.save.call_args.args[0]
        assert isinstance(saved, RawPayload)
        assert saved.provider == "airbnb"
        assert saved.source_url == job.source_url
        assert saved.source_id == "12345"
        assert saved.payload == {"id": "12345", "name": "Cozy flat"}

    @pytest.mark.asyncio
    async def test_raw_payload_skipped_when_repo_is_none(self):
        """process_job does not attempt persistence when raw_payload_repo is None."""
        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        adapter_result = AdapterResult(raw={"id": "12345"}, listing=listing)
        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=adapter_result)

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        # No raw_payload_repo passed — should complete without error
        with patch("src.jobs.processor.send_message", new_callable=AsyncMock):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
                raw_payload_repo=None,
            )
        # No assertion needed — absence of AttributeError is the test

    @pytest.mark.asyncio
    async def test_save_error_does_not_block_pipeline(self):
        """A save failure is swallowed; the analysis and send still complete."""
        job = _make_job()
        listing = _make_listing()
        result = _make_result()
        settings = _make_settings()

        adapter_result = AdapterResult(raw={"id": "12345"}, listing=listing)
        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=adapter_result)

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        failing_repo = AsyncMock()
        failing_repo.save = AsyncMock(side_effect=RuntimeError("DB connection lost"))

        sent_chats: list[int] = []

        async def fake_send(token, chat_id, text, *, client=None):
            sent_chats.append(chat_id)

        with patch("src.jobs.processor.send_message", side_effect=fake_send):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
                raw_payload_repo=failing_repo,
            )

        # Pipeline completed despite save failure
        assert sent_chats == [job.telegram_context.chat_id]

    @pytest.mark.asyncio
    async def test_raw_payload_source_id_none_when_listing_source_id_empty(self):
        """source_id is stored as None when the listing source_id is an empty string."""
        job = _make_job()
        listing = NormalizedListing(
            provider=ListingProvider.AIRBNB,
            source_url="https://www.airbnb.com/rooms/12345",
            source_id="",  # empty
            title="Test listing",
        )
        result = _make_result()
        settings = _make_settings()

        adapter_result = AdapterResult(raw={}, listing=listing)
        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(return_value=adapter_result)

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=result)

        mock_repo = AsyncMock()

        with patch("src.jobs.processor.send_message", new_callable=AsyncMock):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=_make_passthrough_ts(),
                raw_payload_repo=mock_repo,
            )

        saved: RawPayload = mock_repo.save.call_args.args[0]
        assert saved.source_id is None


# ---------------------------------------------------------------------------
# Worker runtime path: process_once wires the DB repo
# ---------------------------------------------------------------------------


def _make_mock_session_factory():
    """Return a mock async_sessionmaker whose sessions are AsyncMock objects."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    session_factory = MagicMock()
    session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    session_factory.return_value.__aexit__ = AsyncMock(return_value=False)
    return session_factory, mock_session


class TestProcessOnceWorkerWiring:
    """process_once must pass a SQLAlchemyRawPayloadRepository to process_job
    when a session_factory is provided, and commit the session afterwards."""

    @pytest.mark.asyncio
    async def test_process_once_passes_raw_payload_repo_to_process_job(self):
        """When session_factory is given, process_job receives a repo instance."""
        from src.domain.listing import AnalysisJob, ListingProvider
        from src.jobs.worker import process_once
        from src.storage.sqlalchemy_repos import SQLAlchemyRawPayloadRepository

        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/1",
            provider=ListingProvider.AIRBNB,
            delivery_channel=DeliveryChannel.TELEGRAM,
            telegram_context=TelegramDeliveryContext(chat_id=1, message_id=1),
        )
        session_factory, mock_session = _make_mock_session_factory()
        redis = AsyncMock()

        settings = _make_settings()

        captured_kwargs: dict = {}

        async def fake_process_job(j, s, **kwargs):
            captured_kwargs.update(kwargs)

        with (
            patch("src.jobs.worker.dequeue_analysis_job", new_callable=AsyncMock, return_value=job),
            patch("src.jobs.worker.process_job", side_effect=fake_process_job),
            patch("src.jobs.worker.build_default_providers", return_value=[]),
        ):
            result = await process_once(redis, settings, session_factory=session_factory)

        assert result is True
        assert "raw_payload_repo" in captured_kwargs
        assert isinstance(captured_kwargs["raw_payload_repo"], SQLAlchemyRawPayloadRepository)

    @pytest.mark.asyncio
    async def test_process_once_commits_session_after_job(self):
        """Session is committed after process_job returns."""
        from src.domain.listing import AnalysisJob, ListingProvider
        from src.jobs.worker import process_once

        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/2",
            provider=ListingProvider.AIRBNB,
            delivery_channel=DeliveryChannel.TELEGRAM,
            telegram_context=TelegramDeliveryContext(chat_id=2, message_id=2),
        )
        session_factory, mock_session = _make_mock_session_factory()
        redis = AsyncMock()
        settings = _make_settings()

        with (
            patch("src.jobs.worker.dequeue_analysis_job", new_callable=AsyncMock, return_value=job),
            patch("src.jobs.worker.process_job", new_callable=AsyncMock),
            patch("src.jobs.worker.build_default_providers", return_value=[]),
        ):
            await process_once(redis, settings, session_factory=session_factory)

        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_process_once_without_session_factory_skips_repo(self):
        """When session_factory is None, process_job receives no raw_payload_repo."""
        from src.domain.listing import AnalysisJob, ListingProvider
        from src.jobs.worker import process_once

        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/3",
            provider=ListingProvider.AIRBNB,
            delivery_channel=DeliveryChannel.TELEGRAM,
            telegram_context=TelegramDeliveryContext(chat_id=3, message_id=3),
        )
        redis = AsyncMock()
        settings = _make_settings()

        captured_kwargs: dict = {}

        async def fake_process_job(j, s, **kwargs):
            captured_kwargs.update(kwargs)

        with (
            patch("src.jobs.worker.dequeue_analysis_job", new_callable=AsyncMock, return_value=job),
            patch("src.jobs.worker.process_job", side_effect=fake_process_job),
            patch("src.jobs.worker.build_default_providers", return_value=[]),
        ):
            result = await process_once(redis, settings, session_factory=None)

        assert result is True
        assert captured_kwargs.get("raw_payload_repo") is None


# ---------------------------------------------------------------------------
# CLI: run_worker_process creates engine + session_factory and passes them
# ---------------------------------------------------------------------------


class TestRunWorkerProcessDBWiring:
    """run_worker_process must create a DB engine and session_factory once,
    pass session_factory to run_worker, and dispose the engine on exit."""

    @pytest.mark.asyncio
    async def test_engine_created_from_database_url(self):
        """make_engine is called with settings.database_url."""
        from src.jobs.cli import run_worker_process

        settings = _make_settings(database_url="postgresql://user:pw@db:5432/flat")
        redis = AsyncMock()
        mock_engine = AsyncMock()

        with (
            patch("src.jobs.cli.make_engine", return_value=mock_engine) as mock_make_engine,
            patch("src.jobs.cli.make_session_factory", return_value=MagicMock()),
            patch("src.jobs.cli.run_worker", new_callable=AsyncMock),
        ):
            await run_worker_process(settings=settings, redis=redis)

        mock_make_engine.assert_called_once_with("postgresql://user:pw@db:5432/flat")

    @pytest.mark.asyncio
    async def test_session_factory_passed_to_run_worker(self):
        """run_worker is called with the session_factory created from the engine."""
        from src.jobs.cli import run_worker_process

        settings = _make_settings()
        redis = AsyncMock()
        mock_engine = AsyncMock()
        mock_sf = MagicMock()

        with (
            patch("src.jobs.cli.make_engine", return_value=mock_engine),
            patch("src.jobs.cli.make_session_factory", return_value=mock_sf),
            patch("src.jobs.cli.run_worker", new_callable=AsyncMock) as mock_run_worker,
        ):
            await run_worker_process(settings=settings, redis=redis)

        mock_run_worker.assert_awaited_once_with(redis, settings, session_factory=mock_sf)

    @pytest.mark.asyncio
    async def test_engine_disposed_on_exit(self):
        """engine.dispose() is called even when run_worker completes normally."""
        from src.jobs.cli import run_worker_process

        settings = _make_settings()
        redis = AsyncMock()
        mock_engine = AsyncMock()

        with (
            patch("src.jobs.cli.make_engine", return_value=mock_engine),
            patch("src.jobs.cli.make_session_factory", return_value=MagicMock()),
            patch("src.jobs.cli.run_worker", new_callable=AsyncMock),
        ):
            await run_worker_process(settings=settings, redis=redis)

        mock_engine.dispose.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_engine_disposed_even_on_run_worker_error(self):
        """engine.dispose() is still called when run_worker raises."""
        from src.jobs.cli import run_worker_process

        settings = _make_settings()
        redis = AsyncMock()
        mock_engine = AsyncMock()

        with (
            patch("src.jobs.cli.make_engine", return_value=mock_engine),
            patch("src.jobs.cli.make_session_factory", return_value=MagicMock()),
            patch("src.jobs.cli.run_worker", new_callable=AsyncMock, side_effect=RuntimeError("boom")),
        ):
            with pytest.raises(RuntimeError, match="boom"):
                await run_worker_process(settings=settings, redis=redis)

        mock_engine.dispose.assert_awaited_once()
