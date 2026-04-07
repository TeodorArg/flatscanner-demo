# Evaluation: Track B Corpus Expansion

## Status

- Date created: `2026-04-07`
- Execution status: `TRACK B BASELINE MEASURED`
- Branch/worktree: `feat/047-track-b-corpus-expansion`

## Verified So Far

### 1. Frozen allowlist is implemented

The repo pilot code now resolves this explicit expanded corpus:

- `.specify/memory/constitution.md`
- `AGENTS.md`
- `README_PROCESS_RU.md`
- `PROCESS_OVERVIEW_EN.md`
- `DELIVERY_FLOW_RU.md`
- `docs/README.md`
- `docs/project-idea.md`
- `docs/context-policy.md`
- `docs/lightrag-local-pilot.md`
- `docs/local-memory-sync.md`
- `specs/042-repo-memory-platform-lightrag/spec.md`
- `specs/042-repo-memory-platform-lightrag/plan.md`
- `specs/042-repo-memory-platform-lightrag/evaluation.md`
- `specs/044-lightrag-retrieval-precision/spec.md`
- `specs/044-lightrag-retrieval-precision/evaluation.md`
- `specs/045-retrieval-quality-benchmark/spec.md`
- `src/repo_memory/lightrag_pilot.py`
- `src/repo_memory/pilot_config.py`
- `src/repo_memory/pilot_types.py`
- `src/repo_memory/markdown_chunks.py`
- `src/repo_memory/query_policy.py`
- `src/repo_memory/reference_resolution.py`
- `src/repo_memory/lightrag_runtime.py`
- `src/repo_memory/context_pack.py`
- `tests/test_lightrag_pilot.py`

### 2. Canonical policy is aligned

The same allowlist is now recorded in:

- `docs/context-policy.md`
- `docs/lightrag-local-pilot.md`
- `specs/047-track-b-corpus-expansion/spec.md`
- `specs/047-track-b-corpus-expansion/plan.md`

### 3. Dry-run build resolves the expanded corpus

Command run:

```bash
python scripts/lightrag_pilot.py build --dry-run
```

Observed result:

- resolved corpus size: `18` files
- expanded `Track B` additions: `11` files
- prepared chunk count: `262`
- debug manifest updated at `.lightrag/chunks/pilot_chunks.json`

### 4. Local checks passed

The following checks succeeded:

- `uv sync --extra dev --extra repo_memory`
- `.venv/bin/python -m pytest tests/test_lightrag_pilot.py`
- `python -m py_compile src/repo_memory/lightrag_pilot.py tests/test_lightrag_pilot.py`
- direct Python assertions for:
  - expanded corpus membership
  - implementation-location query prompt bias
  - `.py` reference extraction for `src/` and `tests/` paths

Observed pytest result:

- `28 passed`

## Clean Rebuild Validation

### Clean rebuild succeeded

Command attempted:

```bash
python scripts/lightrag_pilot.py build --clean
```

Current blocker:

- user-side runtime verification confirmed local `Ollama` availability and the
  required models
- `build --clean` completed successfully and returned the final build manifest
- the expanded baseline produced:
  - graph: `739` nodes, `117` edges
  - chunk vectors: `344`
  - full docs: `260`
  - text chunks: `344`

Inference:

- the clean rebuild path is now validated
- the old duplicate-document refresh blocker did not recur on the clean path
- remaining issues are no longer raw environment/corpus blockers

## Track B Benchmark Results

The expanded-corpus benchmark rows were re-run against the clean rebuilt index.

### BQ3B. Local pilot setup and stack definition

- Verdict: `PASS`
- Mode: `mix`
- Prompt:
  - `Where is the local LightRAG pilot setup documented and what stack is fixed there`
- Notes:
  - post-polish pass now returns the exact canonical file pair:
    `docs/lightrag-local-pilot.md` and `docs/context-policy.md`
  - answer is now explicitly file-first and includes the fixed stack/runtime
    facts: `Ollama`, `qwen2.5:1.5b`, `nomic-embed-text`,
    `scripts/lightrag_pilot.py`, local Python environment, and `.lightrag/`
  - the previous README drift is no longer present in the final shaped answer
- Classification:
  - Track B corpus expansion plus setup-answer shaping solved this benchmark row

### BQ5. Local memory mirror versus canonical memory

- Verdict: `PASS`
- Mode: `mix`
- Prompt:
  - `Which documents define local-memory mirror policy versus canonical repository memory`
- Notes:
  - correctly surfaced `docs/local-memory-sync.md`
  - correctly surfaced `docs/context-policy.md`
  - answer is concise, file-first, and decision-usable for the intended
    boundary question
- Classification:
  - Track B corpus expansion solved this benchmark row materially

### BQ8. Retrieval MVP and precision follow-up ownership

- Verdict: `PASS`
- Mode: `mix`
- Prompt:
  - `Which feature defined the retrieval MVP, which feature closed Q3 Q4 Q5 precision regressions, and which feature owns the broader benchmark`
- Notes:
  - post-polish pass now returns the expected canonical feature-memory file set:
    `specs/042-repo-memory-platform-lightrag/spec.md`,
    `specs/042-repo-memory-platform-lightrag/evaluation.md`,
    `specs/044-lightrag-retrieval-precision/spec.md`,
    `specs/044-lightrag-retrieval-precision/evaluation.md`,
    `specs/045-retrieval-quality-benchmark/spec.md`
  - ownership summary is still present, but it is now subordinate to the exact
    file list rather than replacing it
- Classification:
  - Track B corpus expansion plus ownership-answer shaping solved this row

### BQ9. Local pilot setup and stack

- Verdict: `PASS`
- Mode: `mix`
- Prompt:
  - `Where is the local LightRAG pilot setup documented and what stack is fixed there`
- Notes:
  - same post-polish run as `BQ3B`
  - answer is now tightly anchored to the canonical file pair and fixed stack
    facts without generic doc drift
- Classification:
  - setup/stack retrieval for the expanded corpus is now decision-usable

### BQ10. Current pilot implementation location

- Verdict: `PASS`
- Mode: `hybrid`
- Prompt:
  - `Which code and tests implement the current LightRAG pilot behavior`
- Notes:
  - the original `047` pass correctly surfaced the then-current single-module
    implementation contract around `src/repo_memory/lightrag_pilot.py` and
    `tests/test_lightrag_pilot.py`
  - after feature `049`, the canonical implementation-location contract is
    broader and includes the helper modules under `src/repo_memory/`
  - the historical `047` result remains valid for its original baseline, but it
    should not be read as the full post-`049` implementation file set
- Classification:
  - Track B corpus expansion solved the original out-of-corpus gap; later
    structural refactors can still require contract sync without reopening the
    core `047` corpus-alignment decision

## Summary

### Outcome by row

- `BQ3B`: `PASS`
- `BQ5`: `PASS`
- `BQ8`: `PASS`
- `BQ9`: `PASS`
- `BQ10`: `PASS`

### Main conclusion

The `047` corpus expansion achieved its primary goal:

- the previously out-of-corpus Track B targets are now reachable after clean
  rebuild
- all measured Track B rows are now decision-usable after the allowlist and
  file-first shaping pass
- the expanded allowlist is materially aligned with the benchmark

Residual weakness is now limited to:

- some retrieval/extraction noise from the local indexing model

### Recommended next slice

No additional work is required inside `047` for the current acceptance scope.

Any later follow-up should be a separate feature and should target one of:

- broader retrieval-quality improvements beyond the `047` frozen Track B rows
- extraction-quality cleanup for code- and spec-heavy chunks
- model-quality changes for indexing or querying
