"""Analysis module contract.

``ModuleResult`` is the base output type for every analysis module.
``AnalysisModule`` is the Protocol that all module implementations must satisfy.

Provider-specific vs. generic modules
--------------------------------------
A module whose ``supported_providers`` is a non-empty frozenset is
*provider-specific* — it handles only the listed providers.  A module whose
``supported_providers`` is an empty frozenset is *generic* — it works for any
provider and acts as the fallback when no provider-specific implementation is
registered for a given name.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from src.domain.listing import ListingProvider

if TYPE_CHECKING:
    from src.analysis.context import AnalysisContext


# ---------------------------------------------------------------------------
# Result base type
# ---------------------------------------------------------------------------


@dataclass
class ModuleResult:
    """Base output from a single analysis module run.

    Subclasses add module-specific fields.  ``module_name`` allows the
    runner and downstream consumers to identify which module produced each
    result without relying on the concrete type.
    """

    module_name: str


# ---------------------------------------------------------------------------
# Module protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class AnalysisModule(Protocol):
    """Protocol satisfied by every analysis module implementation.

    Modules are stateless with respect to a single run; all context is
    supplied via ``AnalysisContext``.
    """

    @property
    def name(self) -> str:
        """Stable identifier for this module (e.g. ``"ai_summary"``)."""
        ...

    @property
    def supported_providers(self) -> frozenset[ListingProvider]:
        """Providers this module explicitly supports.

        An empty frozenset marks the module as *generic* — it runs for any
        provider and serves as the fallback when no provider-specific
        variant is registered under the same name.
        """
        ...

    async def run(self, ctx: "AnalysisContext") -> ModuleResult:
        """Execute the module against *ctx* and return a typed result.

        Raises any exception on failure; the runner decides how to handle it.
        """
        ...
