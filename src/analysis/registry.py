"""Analysis module registry.

``ModuleRegistry`` stores analysis module implementations and resolves the
best implementation for a given (name, provider) pair at runtime.

Resolution rules
----------------
1. Collect all registered modules whose ``name`` matches the requested name.
2. If any of them lists *provider* in its ``supported_providers``, return the
   first such match (provider-specific wins).
3. Otherwise return the first module whose ``supported_providers`` is empty
   (generic fallback).
4. If nothing matches, return ``None``.

This lets a future "reviews.airbnb" module coexist with a "reviews.generic"
module: Airbnb listings use the specific path; unknown providers fall back
gracefully.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.domain.listing import ListingProvider

if TYPE_CHECKING:
    from src.analysis.module import AnalysisModule

logger = logging.getLogger(__name__)


class ModuleRegistry:
    """Registry of analysis module implementations.

    Modules are keyed by ``name``; multiple variants (provider-specific and
    generic) may share the same name.  Use ``register`` to add them and
    ``resolve`` or ``all_for_provider`` to look them up.
    """

    def __init__(self) -> None:
        # Ordered list of all registered modules.  Order matters for tie-
        # breaking: first registered wins within the same specificity tier.
        self._modules: list["AnalysisModule"] = []

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, module: "AnalysisModule") -> None:
        """Add *module* to the registry.

        A module is allowed to be registered multiple times (e.g. reloaded
        during tests), but duplicate registrations are skipped to keep the
        registry predictable.
        """
        for existing in self._modules:
            if existing is module:
                return
        self._modules.append(module)
        logger.debug(
            "Registered analysis module %r (providers=%r)",
            module.name,
            module.supported_providers or "generic",
        )

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def resolve(
        self,
        name: str,
        provider: ListingProvider,
    ) -> "AnalysisModule | None":
        """Return the best module implementation for *name* and *provider*.

        Provider-specific beats generic.  Returns ``None`` when no module is
        registered under *name*.
        """
        candidates = [m for m in self._modules if m.name == name]
        if not candidates:
            return None

        # Prefer provider-specific
        for module in candidates:
            if provider in module.supported_providers:
                return module

        # Fall back to generic
        for module in candidates:
            if not module.supported_providers:
                return module

        return None

    def all_for_provider(self, provider: ListingProvider) -> list["AnalysisModule"]:
        """Return one module per registered name, resolved for *provider*.

        Modules whose name resolves to ``None`` for *provider* are excluded.
        The list preserves the registration order of distinct names.
        """
        seen_names: list[str] = []
        result: list["AnalysisModule"] = []
        for module in self._modules:
            if module.name not in seen_names:
                seen_names.append(module.name)
                resolved = self.resolve(module.name, provider)
                if resolved is not None:
                    result.append(resolved)
        return result
