# Tasks: 018-analysis-module-framework

## Status: done

| # | Task | State |
|---|---|---|
| 1 | Create spec, plan, tasks files | done |
| 2 | `src/analysis/context.py` - `AnalysisContext` | done |
| 3 | `src/analysis/module.py` - `ModuleResult` + `AnalysisModule` Protocol | done |
| 4 | `src/analysis/registry.py` - `ModuleRegistry` | done |
| 5 | `src/analysis/runner.py` - `ModuleRunner` | done |
| 6 | `src/analysis/modules/ai_summary.py` - `AISummaryModule` + `AISummaryResult` | done |
| 7 | Update `src/analysis/__init__.py` exports | done |
| 8 | `tests/test_analysis_module_framework.py` - focused tests | done |
| 9 | Add `raw_payload` field to `AnalysisContext` | done |
| 10 | Route `process_job` analysis step through framework (registry + runner) | done |
| 11 | Add framework integration tests in `test_job_processor.py` | done |
| 12 | Update durable docs/spec to match live framework wiring | done |
| 13 | All tests pass | done |
