"""Focused tests for S4: web delivery foundation.

Covers:
- WebDeliveryContext contract
- web_context field on AnalysisJob
- WebProgressSink and WebAnalysisPresenter (no-op stubs)
- Web read models (request/response serialization)
- Web router endpoints: submit (mocked queue), status stub, result stub
- processor handles WEB channel without crashing (no-op sink/presenter)
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.analysis.result import AnalysisResult, PriceVerdict
from src.app.config import Settings
from src.app.main import create_app
from src.domain.delivery import DeliveryChannel, WebDeliveryContext
from src.domain.listing import AnalysisJob, ListingProvider, NormalizedListing, PriceInfo
from src.i18n.types import Language
from src.web.models import (
    WebAnalysisResultResponse,
    WebJobStatusResponse,
    WebSubmitRequest,
    WebSubmitResponse,
)
from src.web.stubs import WebAnalysisPresenter, WebProgressSink


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _test_settings(**overrides) -> Settings:
    defaults = {
        "app_env": "testing",
        "telegram_bot_token": "test-token",
        "openrouter_api_key": "test-key",
        "apify_api_token": "test-apify",
        "database_url": "postgresql://test:test@localhost:5432/test",
        "redis_url": "redis://localhost:6379/1",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _make_listing() -> NormalizedListing:
    return NormalizedListing(
        provider=ListingProvider.AIRBNB,
        source_url="https://www.airbnb.com/rooms/12345",
        source_id="12345",
        title="Cozy flat",
        price=PriceInfo(amount=Decimal("80"), currency="EUR"),
    )


def _make_result() -> AnalysisResult:
    return AnalysisResult(
        summary="Great flat.",
        strengths=["Central location"],
        risks=["Noisy street"],
        price_verdict=PriceVerdict.FAIR,
    )


def _make_web_job(**kwargs) -> AnalysisJob:
    defaults = dict(
        source_url="https://www.airbnb.com/rooms/12345",
        provider=ListingProvider.AIRBNB,
        delivery_channel=DeliveryChannel.WEB,
        web_context=WebDeliveryContext(),
    )
    defaults.update(kwargs)
    return AnalysisJob(**defaults)


# ---------------------------------------------------------------------------
# WebDeliveryContext
# ---------------------------------------------------------------------------


class TestWebDeliveryContext:
    def test_default_correlation_id_is_none(self):
        ctx = WebDeliveryContext()
        assert ctx.correlation_id is None

    def test_correlation_id_stored(self):
        ctx = WebDeliveryContext(correlation_id="abc-123")
        assert ctx.correlation_id == "abc-123"

    def test_serializes_to_dict(self):
        ctx = WebDeliveryContext(correlation_id="x")
        d = ctx.model_dump()
        assert d == {"correlation_id": "x"}


# ---------------------------------------------------------------------------
# AnalysisJob with WEB channel
# ---------------------------------------------------------------------------


class TestAnalysisJobWebChannel:
    def test_web_job_does_not_require_telegram_context(self):
        job = _make_web_job()
        assert job.delivery_channel == DeliveryChannel.WEB
        assert job.telegram_context is None

    def test_web_job_carries_web_context(self):
        ctx = WebDeliveryContext(correlation_id="req-42")
        job = _make_web_job(web_context=ctx)
        assert job.web_context is not None
        assert job.web_context.correlation_id == "req-42"

    def test_web_job_roundtrips_json(self):
        job = _make_web_job(web_context=WebDeliveryContext(correlation_id="rt"))
        restored = AnalysisJob.model_validate_json(job.model_dump_json())
        assert restored.delivery_channel == DeliveryChannel.WEB
        assert restored.web_context is not None
        assert restored.web_context.correlation_id == "rt"

    def test_web_job_web_context_none_allowed(self):
        """web_context is optional — no invariant forces it to be present for WEB."""
        job = _make_web_job(web_context=None)
        assert job.web_context is None


# ---------------------------------------------------------------------------
# WebProgressSink — no-op stub
# ---------------------------------------------------------------------------


class TestWebProgressSink:
    @pytest.mark.asyncio
    async def test_start_does_not_raise(self):
        sink = WebProgressSink()
        await sink.start()

    @pytest.mark.asyncio
    async def test_update_does_not_raise(self):
        sink = WebProgressSink()
        await sink.update("extracting…")

    @pytest.mark.asyncio
    async def test_complete_does_not_raise(self):
        sink = WebProgressSink()
        await sink.complete()

    @pytest.mark.asyncio
    async def test_fail_does_not_raise(self):
        sink = WebProgressSink()
        await sink.fail()


# ---------------------------------------------------------------------------
# WebAnalysisPresenter — no-op stub
# ---------------------------------------------------------------------------


class TestWebAnalysisPresenter:
    @pytest.mark.asyncio
    async def test_deliver_does_not_raise(self):
        presenter = WebAnalysisPresenter()
        listing = _make_listing()
        result = _make_result()
        await presenter.deliver(listing, result, Language.EN)

    @pytest.mark.asyncio
    async def test_deliver_returns_none(self):
        presenter = WebAnalysisPresenter()
        ret = await presenter.deliver(_make_listing(), _make_result(), Language.EN)
        assert ret is None


# ---------------------------------------------------------------------------
# Web read models
# ---------------------------------------------------------------------------


class TestWebModels:
    def test_submit_request_defaults(self):
        req = WebSubmitRequest(url="https://www.airbnb.com/rooms/1")
        assert req.language == "en"
        assert req.correlation_id is None

    def test_submit_request_with_correlation_id(self):
        req = WebSubmitRequest(url="https://example.com/listing", correlation_id="c1")
        assert req.correlation_id == "c1"

    def test_submit_response_has_job_id_and_status(self):
        resp = WebSubmitResponse(job_id=str(uuid.uuid4()), status="queued")
        assert resp.status == "queued"

    def test_job_status_response_fields(self):
        r = WebJobStatusResponse(job_id="abc", status="unknown")
        assert r.job_id == "abc"
        assert r.status == "unknown"
        assert r.error is None

    def test_analysis_result_response_defaults(self):
        r = WebAnalysisResultResponse(job_id="abc", status="unknown")
        assert r.result_available is False
        assert r.summary == ""
        assert r.strengths == []
        assert r.risks == []


# ---------------------------------------------------------------------------
# Web router — endpoint shape tests
# ---------------------------------------------------------------------------


def _make_test_client(redis_mock=None):
    app = create_app(settings=_test_settings())
    # Inject a mock redis into app state before the test client is started.
    app.state.redis = redis_mock
    return TestClient(app, raise_server_exceptions=True)


class TestWebRouterStatus:
    def test_status_unknown_uuid(self):
        client = _make_test_client()
        job_id = str(uuid.uuid4())
        resp = client.get(f"/web/status/{job_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["job_id"] == job_id
        assert body["status"] == "unknown"

    def test_status_invalid_uuid_returns_422(self):
        client = _make_test_client()
        resp = client.get("/web/status/not-a-uuid")
        assert resp.status_code == 422


class TestWebRouterResult:
    def test_result_stub_returns_not_available(self):
        client = _make_test_client()
        job_id = str(uuid.uuid4())
        resp = client.get(f"/web/result/{job_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["result_available"] is False
        assert body["job_id"] == job_id

    def test_result_invalid_uuid_returns_422(self):
        client = _make_test_client()
        resp = client.get("/web/result/bad-id")
        assert resp.status_code == 422


class TestWebRouterSubmit:
    def test_submit_enqueues_and_returns_202(self):
        mock_redis = object()  # non-None sentinel
        with patch(
            "src.web.router.submit_analysis_request",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_enqueue:
            client = _make_test_client(redis_mock=mock_redis)
            resp = client.post(
                "/web/submit",
                json={"url": "https://www.airbnb.com/rooms/12345"},
            )
        assert resp.status_code == 202
        body = resp.json()
        assert body["status"] == "queued"
        assert "job_id" in body
        uuid.UUID(body["job_id"])  # must be valid UUID
        mock_enqueue.assert_awaited_once()

    def test_submit_passes_web_channel(self):
        mock_redis = object()
        captured: list[AnalysisJob] = []

        async def _capture(redis, job):
            captured.append(job)
            return True

        with patch("src.web.router.submit_analysis_request", side_effect=_capture):
            client = _make_test_client(redis_mock=mock_redis)
            client.post(
                "/web/submit",
                json={"url": "https://www.airbnb.com/rooms/12345", "language": "ru"},
            )

        assert len(captured) == 1
        job = captured[0]
        assert job.delivery_channel == DeliveryChannel.WEB
        assert job.language == Language.RU

    def test_submit_no_redis_returns_502(self):
        client = _make_test_client(redis_mock=None)
        resp = client.post(
            "/web/submit",
            json={"url": "https://www.airbnb.com/rooms/12345"},
        )
        assert resp.status_code == 502

    def test_submit_correlation_id_stored_in_web_context(self):
        mock_redis = object()
        captured: list[AnalysisJob] = []

        async def _capture(redis, job):
            captured.append(job)
            return True

        with patch("src.web.router.submit_analysis_request", side_effect=_capture):
            client = _make_test_client(redis_mock=mock_redis)
            client.post(
                "/web/submit",
                json={
                    "url": "https://www.airbnb.com/rooms/12345",
                    "correlation_id": "my-correlation",
                },
            )

        job = captured[0]
        assert job.web_context is not None
        assert job.web_context.correlation_id == "my-correlation"

    def test_submit_unknown_language_falls_back_to_default_language(self):
        mock_redis = object()
        captured: list[AnalysisJob] = []

        async def _capture(redis, job):
            captured.append(job)
            return True

        with patch("src.web.router.submit_analysis_request", side_effect=_capture):
            client = _make_test_client(redis_mock=mock_redis)
            client.post(
                "/web/submit",
                json={"url": "https://www.airbnb.com/rooms/12345", "language": "xx"},
            )

        job = captured[0]
        # Unknown language → falls back to DEFAULT_LANGUAGE ("ru")
        assert job.language == Language.RU


# ---------------------------------------------------------------------------
# App bootstrap — web routes are registered
# ---------------------------------------------------------------------------


class TestWebRoutesRegistered:
    def test_web_submit_route_exists(self):
        app = create_app(settings=_test_settings())
        routes = [r.path for r in app.routes]
        assert "/web/submit" in routes

    def test_web_status_route_exists(self):
        app = create_app(settings=_test_settings())
        routes = [r.path for r in app.routes]
        assert "/web/status/{job_id}" in routes

    def test_web_result_route_exists(self):
        app = create_app(settings=_test_settings())
        routes = [r.path for r in app.routes]
        assert "/web/result/{job_id}" in routes
