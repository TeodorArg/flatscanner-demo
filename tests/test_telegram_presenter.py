"""Focused tests for the Telegram final-result presenter (S3)."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from src.analysis.result import AnalysisResult, PriceVerdict
from src.domain.listing import ListingProvider, NormalizedListing, PriceInfo
from src.i18n.types import Language
from src.telegram.presenter import TelegramAnalysisPresenter


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


class TestTelegramAnalysisPresenter:
    @pytest.mark.asyncio
    async def test_formats_and_sends_message(self):
        listing = _make_listing()
        result = _make_result()

        with patch(
            "src.telegram.presenter.send_message",
            new_callable=AsyncMock,
        ) as mock_send:
            presenter = TelegramAnalysisPresenter("bot-token", 1001)
            await presenter.deliver(listing, result, Language.EN)

        mock_send.assert_awaited_once()
        args, kwargs = mock_send.call_args
        assert args[0] == "bot-token"
        assert args[1] == 1001
        assert "Cozy flat in Berlin" in args[2]
        assert "A pleasant flat in central Berlin." in args[2]
        assert kwargs["client"] is None
