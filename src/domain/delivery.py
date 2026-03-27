"""Delivery-channel abstractions for the analysis platform.

These types establish the seam between the channel-agnostic analysis engine
and concrete delivery implementations such as Telegram or a future Web UI.

The module intentionally has no runtime dependencies on Telegram or any other
channel so that the core platform can import it freely.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import BaseModel

if TYPE_CHECKING:
    from src.analysis.result import AnalysisResult
    from src.domain.listing import NormalizedListing
    from src.i18n.types import Language


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


class WebDeliveryContext(BaseModel):
    """Web-channel delivery metadata attached to a channel-neutral job.

    Carries an optional correlation identifier that the web layer can use to
    track progress and fetch results.  All fields are optional for S4; the
    model is intentionally minimal and will grow as the web channel matures.
    """

    # Caller-supplied opaque identifier used to correlate the request with its
    # result (e.g. a browser session token or a UUID generated at submit time).
    # ``None`` means the caller did not provide one.
    correlation_id: str | None = None


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

    async def complete(self) -> None:
        """Called when the pipeline finishes successfully.

        Implementations should remove any transient progress indicator and
        stop background activity started in ``start()``.  On Telegram this
        deletes the progress message so the final result message stands alone.
        """
        ...

    async def fail(self) -> None:
        """Called when the pipeline terminates with an error.

        Implementations should clean up the same resources as ``complete()``
        but may additionally surface an error indicator.  On Telegram this
        deletes the progress message.
        """
        ...


@runtime_checkable
class AnalysisResultPresenter(Protocol):
    """Channel-specific interface for presenting a completed analysis result.

    The analysis engine produces a structured canonical result.  Concrete
    delivery channels are responsible for rendering and delivering that result
    to the user in their own format (Telegram message, future Web DTO, etc.).
    """

    async def deliver(
        self,
        listing: "NormalizedListing",
        result: "AnalysisResult",
        language: "Language",
    ) -> None:
        """Render and deliver the final analysis result for one channel."""
        ...
