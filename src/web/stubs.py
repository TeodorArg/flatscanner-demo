"""No-op ProgressSink and AnalysisResultPresenter for the web delivery channel.

These stubs satisfy the ``ProgressSink`` and ``AnalysisResultPresenter``
protocols without performing any I/O.  They are used as the default
implementations for WEB-channel jobs until a real web result-storage backend
is wired up in a later slice.

All methods are intentionally no-ops: the web channel will eventually
persist progress state so that clients can poll ``GET /web/status/{job_id}``,
but that persistence layer is out of scope for S4.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.analysis.result import AnalysisResult
    from src.domain.listing import NormalizedListing
    from src.i18n.types import Language


class WebProgressSink:
    """No-op progress sink for WEB-channel jobs.

    Satisfies the ``ProgressSink`` protocol.  All methods are no-ops in S4;
    a future slice will persist stage updates to the database so web clients
    can poll for progress.
    """

    async def start(self) -> None:
        pass

    async def update(self, text: str) -> None:
        pass

    async def complete(self) -> None:
        pass

    async def fail(self) -> None:
        pass


class WebAnalysisPresenter:
    """No-op result presenter for WEB-channel jobs.

    Satisfies the ``AnalysisResultPresenter`` protocol.  The ``deliver``
    method is a no-op in S4; a future slice will persist the structured
    result to the database so it can be served by ``GET /web/result/{job_id}``.
    """

    async def deliver(
        self,
        listing: "NormalizedListing",
        result: "AnalysisResult",
        language: "Language",
    ) -> None:
        pass
