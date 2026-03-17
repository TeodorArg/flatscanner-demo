"""Enrichment runner: tolerant orchestration of external context providers.

``run_enrichments`` fans out to all registered providers concurrently,
collects successful results, records failures and timeouts separately, and
**never raises** — a partially-enriched listing is always better than a
failed pipeline.

Usage example::

    outcome = await run_enrichments(listing, providers, timeout=5.0)
    for r in outcome.successes:
        print(r.name, r.data)
    for r in outcome.failures:
        print(r.name, r.error)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from src.domain.listing import NormalizedListing

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provider protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class EnrichmentProvider(Protocol):
    """Protocol satisfied by any enrichment provider."""

    @property
    def name(self) -> str:
        """A short, stable identifier for this provider (e.g. ``"transit"``)."""
        ...

    async def enrich(self, listing: NormalizedListing) -> dict[str, Any]:
        """Return enrichment data for *listing*.

        Raises any exception on failure; the runner catches it.
        """
        ...


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class EnrichmentProviderResult:
    """Outcome for a single provider run."""

    name: str
    data: dict[str, Any] | None = None
    error: Exception | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


@dataclass
class EnrichmentOutcome:
    """Aggregated outcome for all providers run against a listing."""

    successes: list[EnrichmentProviderResult] = field(default_factory=list)
    failures: list[EnrichmentProviderResult] = field(default_factory=list)

    @property
    def all_failed(self) -> bool:
        """True when every provider failed (and at least one was attempted)."""
        return bool(self.failures) and not self.successes


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


async def run_enrichments(
    listing: NormalizedListing,
    providers: list[EnrichmentProvider],
    *,
    timeout: float = 10.0,
) -> EnrichmentOutcome:
    """Run *providers* concurrently against *listing*, tolerating failures.

    Each provider is wrapped in ``asyncio.wait_for`` so a slow provider
    does not block the pipeline indefinitely.  Timeouts and exceptions are
    recorded as failures; they never propagate.

    Parameters
    ----------
    listing:
        The normalized listing to enrich.
    providers:
        Enrichment providers to invoke.  An empty list is valid and returns
        an empty ``EnrichmentOutcome``.
    timeout:
        Per-provider timeout in seconds.

    Returns
    -------
    EnrichmentOutcome
        Always returned, even when every provider fails.
    """
    if not providers:
        return EnrichmentOutcome()

    async def _run_one(provider: EnrichmentProvider) -> EnrichmentProviderResult:
        try:
            data = await asyncio.wait_for(
                provider.enrich(listing), timeout=timeout
            )
            logger.debug(
                "Enrichment provider %r succeeded for listing %s",
                provider.name,
                listing.id,
            )
            return EnrichmentProviderResult(name=provider.name, data=data)
        except asyncio.TimeoutError as exc:
            logger.warning(
                "Enrichment provider %r timed out for listing %s",
                provider.name,
                listing.id,
            )
            return EnrichmentProviderResult(name=provider.name, error=exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Enrichment provider %r failed for listing %s: %s",
                provider.name,
                listing.id,
                exc,
            )
            return EnrichmentProviderResult(name=provider.name, error=exc)

    results = await asyncio.gather(*(_run_one(p) for p in providers))

    outcome = EnrichmentOutcome()
    for result in results:
        if result.succeeded:
            outcome.successes.append(result)
        else:
            outcome.failures.append(result)

    logger.info(
        "Enrichment complete for listing %s: %d succeeded, %d failed",
        listing.id,
        len(outcome.successes),
        len(outcome.failures),
    )
    return outcome
