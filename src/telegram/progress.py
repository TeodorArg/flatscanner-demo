"""Telegram implementation of the ProgressSink interface.

``TelegramProgressSink`` drives the progress message UX that a user sees
while a listing analysis runs:

- A typing heartbeat keeps Telegram showing the "typing…" indicator.
- Stage updates edit the progress message in place.
- Cleanup deletes the progress message and cancels the heartbeat.

All operations are best-effort: failures are logged at DEBUG level and never
propagated to the caller.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from src.telegram.sender import delete_message, edit_message_text, send_chat_action

if TYPE_CHECKING:
    import httpx

logger = logging.getLogger(__name__)


class TelegramProgressSink:
    """ProgressSink that manages a Telegram progress message and typing heartbeat.

    Parameters
    ----------
    token:
        Telegram bot token used for all API calls.
    chat_id:
        Telegram chat to target.
    progress_message_id:
        ID of the progress message to edit/delete, or ``None`` when no
        progress message exists (all stage updates become no-ops).
    client:
        Optional ``httpx.AsyncClient`` for testing without network calls.
    """

    def __init__(
        self,
        token: str,
        chat_id: int,
        progress_message_id: int | None,
        *,
        client: "httpx.AsyncClient | None" = None,
    ) -> None:
        self._token = token
        self._chat_id = chat_id
        self._progress_message_id = progress_message_id
        self._client = client
        self._heartbeat: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # ProgressSink protocol
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the typing heartbeat background task."""
        self._heartbeat = asyncio.create_task(self._run_heartbeat())

    async def update(self, text: str) -> None:
        """Edit the progress message with *text*. No-op if no message id."""
        if self._progress_message_id is None:
            return
        try:
            await edit_message_text(
                self._token,
                self._chat_id,
                self._progress_message_id,
                text,
                client=self._client,
            )
        except Exception:
            logger.debug(
                "Progress update failed for chat_id=%s msg_id=%s (best-effort, ignored)",
                self._chat_id,
                self._progress_message_id,
                exc_info=True,
            )

    async def cleanup(self) -> None:
        """Delete the progress message and cancel the typing heartbeat."""
        if self._progress_message_id is not None:
            try:
                await delete_message(
                    self._token,
                    self._chat_id,
                    self._progress_message_id,
                    client=self._client,
                )
            except Exception:
                logger.debug(
                    "Progress message deletion failed for chat_id=%s msg_id=%s (best-effort, ignored)",
                    self._chat_id,
                    self._progress_message_id,
                    exc_info=True,
                )
        if self._heartbeat is not None:
            self._heartbeat.cancel()
            try:
                await self._heartbeat
            except asyncio.CancelledError:
                pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _run_heartbeat(self) -> None:
        """Send a ``typing`` chat action every 4 s until cancelled."""
        while True:
            try:
                await send_chat_action(self._token, self._chat_id, client=self._client)
            except Exception:
                pass  # best-effort
            await asyncio.sleep(4)
