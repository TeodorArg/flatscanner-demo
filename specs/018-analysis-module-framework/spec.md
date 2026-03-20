# Feature Spec: Analysis Module Framework (P3)

## Context

This is P3 of the post-MVP migration defined in `specs/015-post-mvp-architecture-foundation/spec.md`
and ADR 004.

The MVP shipped a single `AnalysisService.analyse()` path. Adding multiple analysis modules
(reviews, price, host, location, amenities, policies) requires a structured registry and runner so
modules can be added independently and providers can have both specific and generic fallback
implementations.

## Scope

Implement the analysis module framework as the first live compatibility layer:

- `AnalysisContext` bundles listing, enrichment outcome, raw payload, and provider accessor.
- `ModuleResult` / `AnalysisModule` define the typed contract for module implementations.
- `ModuleRegistry` registers modules keyed by name and optional provider; resolves with
  provider-specific preference and generic fallback.
- `ModuleRunner` runs all registered modules against a context and collects results.
- `AISummaryModule` wraps the existing `AnalysisService` logic as the first registered module.
- Existing `AnalysisService.analyse()` and `AnalysisResult` behavior remain unchanged.
- The live `process_job` analysis step routes through the framework while preserving the same
  user-visible output and downstream translation/formatting behavior.

## Out of Scope

- New analysis modules beyond `AISummaryModule` (P4+).
- Analysis result cache (P5).
- Module-specific persistence beyond raw payload capture already completed in P2.

## Contracts

### AnalysisContext

```python
@dataclass
class AnalysisContext:
    listing: NormalizedListing
    enrichment: EnrichmentOutcome | None = None
    raw_payload: RawPayload | None = None

    @property
    def provider(self) -> ListingProvider: ...
```

### ModuleResult

```python
@dataclass
class ModuleResult:
    module_name: str
```

### AnalysisModule (Protocol)

```python
class AnalysisModule(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def supported_providers(self) -> frozenset[ListingProvider]: ...
    # empty frozenset = generic (works for all providers)

    async def run(self, ctx: AnalysisContext) -> ModuleResult: ...
```

### ModuleRegistry

```python
class ModuleRegistry:
    def register(self, module: AnalysisModule) -> None: ...
    def resolve(self, name: str, provider: ListingProvider) -> AnalysisModule | None: ...
    def all_for_provider(self, provider: ListingProvider) -> list[AnalysisModule]: ...
```

### ModuleRunner

```python
class ModuleRunner:
    def __init__(self, registry: ModuleRegistry) -> None: ...
    async def run(self, ctx: AnalysisContext) -> list[ModuleResult]: ...
```

### AISummaryModule

- `name = "ai_summary"`
- `supported_providers = frozenset()` (generic)
- `run(ctx)` delegates to `AnalysisService.analyse(ctx.listing, ctx.enrichment)`
- Returns `AISummaryResult(module_name="ai_summary", analysis_result=<AnalysisResult>)`

### Live Pipeline Wiring

- `process_job` builds `AnalysisContext(listing, enrichment, raw_payload)`
- `process_job` registers `AISummaryModule` in `ModuleRegistry`
- `ModuleRunner` executes the registry for the listing provider
- `AISummaryResult.analysis_result` continues through translation, formatting, and Telegram
  delivery unchanged from the caller perspective

## Acceptance Criteria

- Framework files compile and are importable.
- Existing tests pass unchanged.
- New focused tests cover: context provider accessor, registry resolution
  (provider-specific beats generic, generic fallback, unknown name -> `None`), runner collects
  results from all registered modules, and `AISummaryModule` wraps `AnalysisService` correctly.
- Job processor integration tests prove the live analysis step now runs through
  `ModuleRegistry` + `ModuleRunner` while preserving the existing `AnalysisResult`-driven flow.
