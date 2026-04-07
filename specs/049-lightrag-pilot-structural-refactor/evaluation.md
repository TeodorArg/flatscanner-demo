# Evaluation: LightRAG Pilot Structural Refactor

## Status

- Date: `2026-04-07`
- Execution status: `STRUCTURAL REFACTOR VALIDATED`
- Branch/worktree: `feat/049-lightrag-pilot-structural-refactor`

## Validation Scope

This note records the post-refactor validation for feature `049`.

Validation target:

- confirm that the `lightrag_pilot` module split remains behavior-compatible
- confirm that the thin facade stays public and usable
- confirm that the implementation-location contract is synchronized after the
  facade split
- confirm that the benchmark-relevant rows do not regress after the structural
  refactor

## Structural Outcome

The refactor split the former monolithic `src/repo_memory/lightrag_pilot.py`
into these modules:

- `src/repo_memory/lightrag_pilot.py`
- `src/repo_memory/pilot_config.py`
- `src/repo_memory/pilot_types.py`
- `src/repo_memory/markdown_chunks.py`
- `src/repo_memory/query_policy.py`
- `src/repo_memory/reference_resolution.py`
- `src/repo_memory/lightrag_runtime.py`
- `src/repo_memory/context_pack.py`

Result:

- facade size reduced from `1366` lines to `269` lines
- public entrypoint path `src.repo_memory.lightrag_pilot:main` remains stable
- helper symbols used by the current regression tests continue to re-export via
  the facade

## Automated Checks

The following checks passed in the `049` worktree:

- `/Users/svarnoy85/teodorArg/flatscanner-demo/.venv/bin/python -m pytest tests/test_lightrag_pilot.py`
  - result: `32 passed`
- `/Users/svarnoy85/teodorArg/flatscanner-demo/.venv/bin/python scripts/lightrag_pilot.py build --dry-run`
  - result: dry-run completed successfully with the synchronized expanded
    allowlist

## Corpus And Rebuild Validation

Post-sync clean rebuild completed successfully on the updated implementation
contract.

Observed rebuilt index state:

- graph: `800` nodes, `123` edges
- full docs: `284`
- text chunks: `394`

Interpretation:

- the index is larger than the pre-`049` baseline because the canonical
  implementation-location contract now includes the helper modules extracted
  from the former monolith
- this is expected contract sync, not unintended benchmark drift

## Benchmark Rerun Summary

The following benchmark-relevant rows were re-run after the structural refactor
and contract sync:

- `BQ2` read order
  - `PASS`
- `BQ3A` pilot boundary / corpus policy
  - `PASS`
- `BQ6` generic PR-loop contract
  - `PASS`
- `BQ7` PR-loop completion conditions
  - `PASS`
- `BQ3B` / `BQ9` local pilot setup and stack
  - `PASS`
- `BQ8` retrieval ownership
  - `PASS`
- `BQ10` current pilot implementation location
  - `PASS`

## BQ10 Contract Sync Note

The only real post-refactor drift risk was `BQ10`.

Cause:

- before `049`, the implementation-location benchmark contract assumed that the
  pilot behavior lived mainly in `src/repo_memory/lightrag_pilot.py` plus
  `tests/test_lightrag_pilot.py`
- after the structural split, that assumption became false unless the allowlist,
  benchmark docs, and answer-shaping logic were updated together

Resolution applied inside `049`:

- expanded implementation-location allowlist now includes the helper modules
  under `src/repo_memory/`
- `docs/context-policy.md` and `docs/lightrag-local-pilot.md` now describe the
  multi-module implementation contract
- `specs/045` and `specs/047` were synchronized so `BQ10` no longer implies a
  stale monolithic implementation model
- implementation-location answer shaping is now explicitly file-first for the
  thin facade plus helper-module set

Result:

- `BQ10` now passes without misrepresenting the current code layout

## Verdict Against `049`

### AC1. The facade is materially smaller

- `PASS`

### AC2. Module boundaries are explicit

- `PASS`

### AC3. Public behavior remains stable

- `PASS`

### AC4. Follow-up work becomes narrower

- `PASS`

## Conclusion

Feature `049` is validated for its intended structural-refactor scope.

The refactor did not introduce benchmark regressions after the
implementation-location contract was synchronized to the new multi-module
layout.
