"""AI summary analysis module.

``AISummaryModule`` is the first registered analysis module.  It wraps the
existing ``AnalysisService`` so the provider-aware module framework can
invoke it alongside future specialist modules (reviews, price, host, …).

The module is *generic* — it works for any listing provider.  Future modules
can override specific behaviour for a given provider while this module
continues to handle the generic fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.analysis.module import ModuleResult
from src.domain.listing import ListingProvider

if TYPE_CHECKING:
    from src.analysis.context import AnalysisContext
    from src.analysis.result import AnalysisResult
    from src.analysis.service import AnalysisService


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class AISummaryResult(ModuleResult):
    """Output from ``AISummaryModule``.

    Wraps the ``AnalysisResult`` produced by ``AnalysisService`` so it can
    travel through the typed module result pipeline.
    """

    analysis_result: "AnalysisResult"


# ---------------------------------------------------------------------------
# Module implementation
# ---------------------------------------------------------------------------


class AISummaryModule:
    """Generic AI summary module backed by ``AnalysisService``.

    Parameters
    ----------
    service:
        Pre-built ``AnalysisService``.  Callers are responsible for
        constructing and configuring it (e.g. with the right OpenRouter
        client and settings).
    """

    name = "ai_summary"
    supported_providers: frozenset[ListingProvider] = frozenset()  # generic

    def __init__(self, service: "AnalysisService") -> None:
        self._service = service

    async def run(self, ctx: "AnalysisContext") -> AISummaryResult:
        """Delegate to ``AnalysisService`` and wrap the result.

        Parameters
        ----------
        ctx:
            Analysis context supplying listing and optional enrichment.

        Returns
        -------
        AISummaryResult
            Typed wrapper around the ``AnalysisResult``.

        Raises
        ------
        OpenRouterError
            Propagated from ``AnalysisService`` on API failure.
        ValueError
            Propagated from ``AnalysisService`` on unparseable model response.
        """
        analysis_result = await self._service.analyse(ctx.listing, ctx.enrichment)
        return AISummaryResult(
            module_name=self.name,
            analysis_result=analysis_result,
        )
