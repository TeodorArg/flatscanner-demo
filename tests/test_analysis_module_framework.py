"""Tests for the P3 analysis module framework.

Covers:
- AnalysisContext: construction, provider accessor
- ModuleResult: base dataclass
- AnalysisModule protocol: structural check
- ModuleRegistry: register, resolve (provider-specific beats generic,
  generic fallback, unknown name → None), all_for_provider, duplicate skip
- ModuleRunner: no modules → empty list, runs all modules concurrently,
  exception propagation
- AISummaryModule: name/supported_providers contract, run() delegates to
  AnalysisService and wraps result in AISummaryResult
"""

from __future__ import annotations

import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.analysis.context import AnalysisContext
from src.analysis.module import AnalysisModule, ModuleResult
from src.analysis.modules.ai_summary import AISummaryModule, AISummaryResult
from src.analysis.registry import ModuleRegistry
from src.analysis.result import AnalysisResult, PriceVerdict
from src.analysis.runner import ModuleRunner
from src.analysis.service import AnalysisService
from src.domain.listing import ListingProvider, NormalizedListing
from src.enrichment.runner import EnrichmentOutcome, EnrichmentProviderResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _listing(provider: ListingProvider = ListingProvider.AIRBNB) -> NormalizedListing:
    return NormalizedListing(
        provider=provider,
        source_url="https://www.airbnb.com/rooms/1",
        source_id="1",
        title="Test Listing",
    )


def _valid_analysis_result() -> AnalysisResult:
    return AnalysisResult(
        summary="Great place.",
        strengths=["Location"],
        risks=["Noisy"],
        price_verdict=PriceVerdict.FAIR,
        price_explanation="Reasonable for the area.",
    )


def _make_service(result: AnalysisResult | None = None) -> AnalysisService:
    """Return a mock AnalysisService that returns *result* from analyse()."""
    svc = MagicMock(spec=AnalysisService)
    svc.analyse = AsyncMock(return_value=result or _valid_analysis_result())
    return svc


def _stub_module(
    name: str,
    providers: frozenset[ListingProvider] = frozenset(),
    result: ModuleResult | None = None,
) -> AnalysisModule:
    """Return a minimal mock module satisfying the AnalysisModule protocol."""
    mod = MagicMock()
    mod.name = name
    mod.supported_providers = providers
    mod.run = AsyncMock(return_value=result or ModuleResult(module_name=name))
    return mod


# ---------------------------------------------------------------------------
# AnalysisContext
# ---------------------------------------------------------------------------


class TestAnalysisContext:
    def test_provider_forwards_from_listing(self):
        listing = _listing(ListingProvider.AIRBNB)
        ctx = AnalysisContext(listing=listing)
        assert ctx.provider == ListingProvider.AIRBNB

    def test_enrichment_defaults_to_none(self):
        ctx = AnalysisContext(listing=_listing())
        assert ctx.enrichment is None

    def test_enrichment_stored_when_supplied(self):
        outcome = EnrichmentOutcome(
            successes=[EnrichmentProviderResult(name="transport", data={"count": 2})]
        )
        ctx = AnalysisContext(listing=_listing(), enrichment=outcome)
        assert ctx.enrichment is outcome

    def test_unknown_provider_forwarded(self):
        listing = _listing(ListingProvider.UNKNOWN)
        ctx = AnalysisContext(listing=listing)
        assert ctx.provider == ListingProvider.UNKNOWN


# ---------------------------------------------------------------------------
# ModuleResult
# ---------------------------------------------------------------------------


class TestModuleResult:
    def test_module_name_stored(self):
        r = ModuleResult(module_name="test_mod")
        assert r.module_name == "test_mod"


# ---------------------------------------------------------------------------
# AnalysisModule protocol structural check
# ---------------------------------------------------------------------------


class TestAnalysisModuleProtocol:
    def test_stub_satisfies_protocol(self):
        mod = _stub_module("x")
        assert isinstance(mod, AnalysisModule)

    def test_ai_summary_module_satisfies_protocol(self):
        mod = AISummaryModule(service=_make_service())
        assert isinstance(mod, AnalysisModule)


# ---------------------------------------------------------------------------
# ModuleRegistry
# ---------------------------------------------------------------------------


class TestModuleRegistryResolve:
    def test_resolve_returns_none_for_unknown_name(self):
        registry = ModuleRegistry()
        assert registry.resolve("nonexistent", ListingProvider.AIRBNB) is None

    def test_resolve_returns_generic_module(self):
        registry = ModuleRegistry()
        generic = _stub_module("reviews")
        registry.register(generic)
        resolved = registry.resolve("reviews", ListingProvider.AIRBNB)
        assert resolved is generic

    def test_resolve_prefers_provider_specific(self):
        registry = ModuleRegistry()
        generic = _stub_module("reviews")
        specific = _stub_module("reviews", providers=frozenset({ListingProvider.AIRBNB}))
        registry.register(generic)
        registry.register(specific)
        resolved = registry.resolve("reviews", ListingProvider.AIRBNB)
        assert resolved is specific

    def test_resolve_falls_back_to_generic_for_other_provider(self):
        registry = ModuleRegistry()
        generic = _stub_module("reviews")
        specific = _stub_module("reviews", providers=frozenset({ListingProvider.AIRBNB}))
        registry.register(generic)
        registry.register(specific)
        resolved = registry.resolve("reviews", ListingProvider.UNKNOWN)
        assert resolved is generic

    def test_resolve_returns_none_when_only_other_provider_specific(self):
        registry = ModuleRegistry()
        airbnb_only = _stub_module("price", providers=frozenset({ListingProvider.AIRBNB}))
        registry.register(airbnb_only)
        # UNKNOWN provider, no generic fallback → None
        resolved = registry.resolve("price", ListingProvider.UNKNOWN)
        assert resolved is None

    def test_duplicate_registration_ignored(self):
        registry = ModuleRegistry()
        mod = _stub_module("dup")
        registry.register(mod)
        registry.register(mod)
        # Only one copy stored
        assert len([m for m in registry._modules if m.name == "dup"]) == 1


class TestModuleRegistryAllForProvider:
    def test_empty_registry_returns_empty(self):
        assert ModuleRegistry().all_for_provider(ListingProvider.AIRBNB) == []

    def test_returns_one_entry_per_name(self):
        registry = ModuleRegistry()
        generic_reviews = _stub_module("reviews")
        specific_reviews = _stub_module("reviews", providers=frozenset({ListingProvider.AIRBNB}))
        generic_price = _stub_module("price")
        registry.register(generic_reviews)
        registry.register(specific_reviews)
        registry.register(generic_price)
        result = registry.all_for_provider(ListingProvider.AIRBNB)
        names = [m.name for m in result]
        assert names == ["reviews", "price"]

    def test_returns_provider_specific_implementation(self):
        registry = ModuleRegistry()
        generic = _stub_module("summary")
        specific = _stub_module("summary", providers=frozenset({ListingProvider.AIRBNB}))
        registry.register(generic)
        registry.register(specific)
        result = registry.all_for_provider(ListingProvider.AIRBNB)
        assert result[0] is specific

    def test_excludes_unresolvable_names(self):
        registry = ModuleRegistry()
        airbnb_only = _stub_module("airbnb_thing", providers=frozenset({ListingProvider.AIRBNB}))
        registry.register(airbnb_only)
        result = registry.all_for_provider(ListingProvider.UNKNOWN)
        assert result == []


# ---------------------------------------------------------------------------
# ModuleRunner
# ---------------------------------------------------------------------------


class TestModuleRunner:
    @pytest.mark.asyncio
    async def test_empty_registry_returns_empty_list(self):
        runner = ModuleRunner(ModuleRegistry())
        ctx = AnalysisContext(listing=_listing())
        results = await runner.run(ctx)
        assert results == []

    @pytest.mark.asyncio
    async def test_runs_all_registered_modules(self):
        registry = ModuleRegistry()
        mod_a = _stub_module("a", result=ModuleResult(module_name="a"))
        mod_b = _stub_module("b", result=ModuleResult(module_name="b"))
        registry.register(mod_a)
        registry.register(mod_b)

        runner = ModuleRunner(registry)
        ctx = AnalysisContext(listing=_listing())
        results = await runner.run(ctx)

        assert len(results) == 2
        assert {r.module_name for r in results} == {"a", "b"}

    @pytest.mark.asyncio
    async def test_result_types_preserved(self):
        registry = ModuleRegistry()
        ai_result = AISummaryResult(
            module_name="ai_summary",
            analysis_result=_valid_analysis_result(),
        )
        mod = _stub_module("ai_summary", result=ai_result)
        registry.register(mod)

        runner = ModuleRunner(registry)
        results = await runner.run(AnalysisContext(listing=_listing()))

        assert len(results) == 1
        assert isinstance(results[0], AISummaryResult)

    @pytest.mark.asyncio
    async def test_exception_from_module_propagates(self):
        registry = ModuleRegistry()
        failing_mod = _stub_module("bad")
        failing_mod.run = AsyncMock(side_effect=RuntimeError("module exploded"))
        registry.register(failing_mod)

        runner = ModuleRunner(registry)
        with pytest.raises(RuntimeError, match="module exploded"):
            await runner.run(AnalysisContext(listing=_listing()))

    @pytest.mark.asyncio
    async def test_only_resolves_modules_for_context_provider(self):
        registry = ModuleRegistry()
        airbnb_only = _stub_module(
            "special", providers=frozenset({ListingProvider.AIRBNB})
        )
        registry.register(airbnb_only)

        runner = ModuleRunner(registry)
        # UNKNOWN provider — no generic fallback, so module is excluded
        ctx = AnalysisContext(listing=_listing(ListingProvider.UNKNOWN))
        results = await runner.run(ctx)
        assert results == []


# ---------------------------------------------------------------------------
# AISummaryModule
# ---------------------------------------------------------------------------


class TestAISummaryModule:
    def test_name_is_ai_summary(self):
        mod = AISummaryModule(service=_make_service())
        assert mod.name == "ai_summary"

    def test_supported_providers_is_empty_frozenset(self):
        mod = AISummaryModule(service=_make_service())
        assert mod.supported_providers == frozenset()

    @pytest.mark.asyncio
    async def test_run_delegates_to_service(self):
        expected = _valid_analysis_result()
        svc = _make_service(result=expected)
        mod = AISummaryModule(service=svc)

        listing = _listing()
        ctx = AnalysisContext(listing=listing)
        result = await mod.run(ctx)

        svc.analyse.assert_awaited_once_with(listing, None)
        assert isinstance(result, AISummaryResult)
        assert result.analysis_result is expected
        assert result.module_name == "ai_summary"

    @pytest.mark.asyncio
    async def test_run_passes_enrichment_to_service(self):
        svc = _make_service()
        mod = AISummaryModule(service=svc)

        enrichment = EnrichmentOutcome(
            successes=[EnrichmentProviderResult(name="transport", data={"count": 1})]
        )
        ctx = AnalysisContext(listing=_listing(), enrichment=enrichment)
        await mod.run(ctx)

        svc.analyse.assert_awaited_once_with(ctx.listing, enrichment)

    @pytest.mark.asyncio
    async def test_run_propagates_service_error(self):
        from src.analysis.openrouter_client import OpenRouterError

        svc = _make_service()
        svc.analyse = AsyncMock(side_effect=OpenRouterError("API down"))
        mod = AISummaryModule(service=svc)

        with pytest.raises(OpenRouterError, match="API down"):
            await mod.run(AnalysisContext(listing=_listing()))

    @pytest.mark.asyncio
    async def test_full_roundtrip_through_registry_and_runner(self):
        """AISummaryModule wired into registry+runner returns AISummaryResult."""
        expected = _valid_analysis_result()
        svc = _make_service(result=expected)
        mod = AISummaryModule(service=svc)

        registry = ModuleRegistry()
        registry.register(mod)
        runner = ModuleRunner(registry)

        ctx = AnalysisContext(listing=_listing())
        results = await runner.run(ctx)

        assert len(results) == 1
        assert isinstance(results[0], AISummaryResult)
        assert results[0].analysis_result.price_verdict == PriceVerdict.FAIR
