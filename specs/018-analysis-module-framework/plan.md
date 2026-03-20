# Implementation Plan: 018-analysis-module-framework

## New files

| File | Purpose |
|---|---|
| `src/analysis/context.py` | `AnalysisContext` dataclass |
| `src/analysis/module.py` | `ModuleResult` dataclass + `AnalysisModule` Protocol |
| `src/analysis/registry.py` | `ModuleRegistry` |
| `src/analysis/runner.py` | `ModuleRunner` |
| `src/analysis/modules/__init__.py` | modules sub-package |
| `src/analysis/modules/ai_summary.py` | `AISummaryModule` + `AISummaryResult` |
| `tests/test_analysis_module_framework.py` | focused framework tests |

## Changed files

| File | Change |
|---|---|
| `src/analysis/__init__.py` | add new symbols to `__all__` |
| `src/jobs/processor.py` | route the live analysis step through registry + runner |
| `tests/test_job_processor.py` | integration coverage for live framework usage |
| `docs/project/backend/backend-docs.md` | record that the framework now fronts the live analysis stage |
| `specs/018-analysis-module-framework/tasks.md` | task state tracking |

## Approach

Additive only for the analysis contracts themselves: no change to the public
`AnalysisService.analyse()` API or `AnalysisResult` shape. The live `process_job`
pipeline now resolves `AISummaryModule` through `ModuleRegistry` + `ModuleRunner`
so later modules can be added without another orchestration refactor.

## Registry resolution logic

1. Collect all modules registered under `name`.
2. If any has `provider` in its `supported_providers`, return it (provider-specific wins).
3. Else return the module whose `supported_providers` is empty (generic fallback).
4. If no match at all, return `None`.
