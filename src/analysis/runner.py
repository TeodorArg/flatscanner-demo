"""Analysis module runner.

``ModuleRunner`` drives all registered modules against an ``AnalysisContext``.
It resolves the best implementation for each module name and *provider*, runs
them concurrently, and returns the collected results.

Like the enrichment runner, module failures are propagated to the caller; the
runner itself does not swallow exceptions — that decision belongs to the
orchestrating layer (e.g. ``process_job``).
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.analysis.context import AnalysisContext
    from src.analysis.module import ModuleResult
    from src.analysis.registry import ModuleRegistry

logger = logging.getLogger(__name__)


class ModuleRunner:
    """Runs all registered analysis modules against an ``AnalysisContext``.

    Parameters
    ----------
    registry:
        The module registry to use for resolving implementations.
    """

    def __init__(self, registry: "ModuleRegistry") -> None:
        self._registry = registry

    async def run(self, ctx: "AnalysisContext") -> list["ModuleResult"]:
        """Run all modules registered for *ctx.provider* concurrently.

        Each module is resolved via the registry (provider-specific preferred,
        generic fallback).  All resolved modules are run concurrently via
        ``asyncio.gather``.  Any exception raised by a module propagates out
        of this call.

        Parameters
        ----------
        ctx:
            Analysis context supplied to every module.

        Returns
        -------
        list[ModuleResult]
            One result per successfully resolved module, in registry order.
        """
        modules = self._registry.all_for_provider(ctx.provider)

        if not modules:
            logger.debug(
                "No analysis modules registered for provider %r", ctx.provider
            )
            return []

        logger.debug(
            "Running %d analysis module(s) for provider %r: %s",
            len(modules),
            ctx.provider,
            [m.name for m in modules],
        )

        results: list["ModuleResult"] = await asyncio.gather(
            *(m.run(ctx) for m in modules)
        )

        logger.info(
            "Analysis modules complete for listing %s: %d result(s)",
            ctx.listing.id,
            len(results),
        )
        return list(results)
