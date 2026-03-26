"""Telegram-specific final-result presenter.

The analysis engine emits a structured ``AnalysisResult``.  This presenter is
responsible for turning that result into Telegram text via the formatter and
delivering it through the Telegram sender helpers.
"""

from __future__ import annotations

import httpx

from src.analysis.result import AnalysisResult
from src.domain.listing import NormalizedListing
from src.i18n.types import Language
from src.telegram.formatter import format_analysis_message
from src.telegram.sender import send_message


class TelegramAnalysisPresenter:
    """Render and deliver the final analysis result to a Telegram chat."""

    def __init__(
        self,
        token: str,
        chat_id: int,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._token = token
        self._chat_id = chat_id
        self._client = client

    async def deliver(
        self,
        listing: NormalizedListing,
        result: AnalysisResult,
        language: Language,
    ) -> None:
        """Format the analysis result and send it to the configured chat."""
        text = format_analysis_message(listing, result, language)
        await send_message(self._token, self._chat_id, text, client=self._client)
