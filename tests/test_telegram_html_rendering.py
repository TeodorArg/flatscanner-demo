"""Focused tests for HTML parse-mode delivery of Telegram analysis messages."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.analysis.result import AnalysisResult, PriceVerdict
from src.domain.listing import ListingProvider, NormalizedListing
from src.i18n.types import Language
from src.telegram.presenter import TelegramAnalysisPresenter
from src.telegram.sender import send_message


def _listing() -> NormalizedListing:
    return NormalizedListing(
        provider=ListingProvider.AIRBNB,
        source_url="https://www.airbnb.com/rooms/12345",
        source_id="12345",
        title="Loft & Light <City>",
    )


def _result() -> AnalysisResult:
    return AnalysisResult(
        display_title="Loft & Light <City>",
        summary="Bright <open> plan & good light.",
        strengths=["Fast Wi-Fi"],
        risks=["Steep stairs"],
        price_verdict=PriceVerdict.FAIR,
        price_explanation="Reasonable for the area.",
    )


class TestTelegramSenderParseMode:
    @pytest.mark.asyncio
    async def test_send_message_includes_parse_mode_when_requested(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response

        await send_message(
            "token",
            123,
            "<b>Hello</b>",
            parse_mode="HTML",
            client=mock_client,
        )

        _, kwargs = mock_client.post.await_args
        assert kwargs["json"]["parse_mode"] == "HTML"


class TestTelegramAnalysisPresenter:
    @pytest.mark.asyncio
    async def test_presenter_sends_final_message_with_html_parse_mode(self):
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response

        presenter = TelegramAnalysisPresenter("token", 123, client=mock_client)
        await presenter.deliver(_listing(), _result(), Language.EN)

        _, kwargs = mock_client.post.await_args
        payload = kwargs["json"]
        assert payload["parse_mode"] == "HTML"
        assert payload["text"].startswith("<b>Loft &amp; Light &lt;City&gt;</b>")
        assert "Bright &lt;open&gt; plan &amp; good light." in payload["text"]
