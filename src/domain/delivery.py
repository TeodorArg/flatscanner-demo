"""Delivery-channel abstractions for the analysis platform.

These types establish the seam between the channel-agnostic analysis engine
and concrete delivery implementations such as Telegram or a future Web UI.

The module intentionally has no runtime dependencies on Telegram or any other
channel so that the core platform can import it freely.
"""

from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel


class DeliveryChannel(str, Enum):
    """Supported delivery channels for analysis results."""

    TELEGRAM = "telegram"
    WEB = "web"


class TelegramDeliveryContext(BaseModel):
    """Telegram-specific delivery metadata attached to a channel-neutral job.

    Carries the identifiers the Telegram delivery layer needs to send progress
    updates and the final result to the correct chat.
    """

    chat_id: int
    message_id: int
    # Set after the initial progress message is sent; None means no progress
    # indicator is active (e.g. when the webhook could not send one).
    progress_message_id: int | None = None


@runtime_checkable
class ProgressSink(Protocol):
    """Channel-neutral interface for reporting pipeline progress to the user.

    The analysis engine calls these methods at well-defined pipeline
    milestones.  Each concrete delivery channel (Telegram, Web, …) provides
    its own implementation.

    All methods are best-effort: implementations must swallow failures
    internally and never propagate exceptions to the caller.
    """

    async def start(self) -> None:
        """Called once when pipeline execution begins.

        Implementations may use this to start background activity (e.g.
        a Telegram typing heartbeat).
        """
        ...

    async def update(self, text: str) -> None:
        """Emit a user-visible stage description.

        Called at each coarse pipeline stage (extracting, enriching,
        analysing, preparing).  *text* is a pre-localised string.
        """
        ...

    async def cleanup(self) -> None:
        """Called in the finally block at the end of pipeline execution.

        Implementations should remove any transient progress indicator and
        stop any background activity started in ``start()``.  This must be
        called whether the pipeline succeeded or failed.
        """
        ...
