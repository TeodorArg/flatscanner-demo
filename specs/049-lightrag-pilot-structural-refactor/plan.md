# Plan: LightRAG Pilot Structural Refactor

## Goal

Разделить `src/repo_memory/lightrag_pilot.py` на набор небольших модулей с
ясными responsibility boundaries, сохранив текущий runtime contract, public
entrypoints и post-`048` retrieval behavior.

## Baseline

Current baseline:

- `src/repo_memory/lightrag_pilot.py` is `1366` lines
- module currently mixes config, types, Markdown chunking, query policy,
  reference resolution, runtime wiring, orchestration, and CLI
- `047` already stabilized the expanded corpus/build baseline
- `048` already stabilized the current narrow retrieval-quality tuning layer

This means the next safe step is structural decomposition, not another behavior
change.

Context7-backed official LightRAG docs confirm that the existing architectural
shape remains valid and should be preserved during the refactor:

- instantiate `LightRAG(...)` programmatically
- use repository-local `working_dir`
- call `initialize_storages()` before operations
- call `finalize_storages()` before exit
- use `QueryParam` for retrieval shaping

## Working Hypothesis

Most current maintenance pain comes from module boundary collapse rather than
from a wrong pilot architecture.

If we extract responsibility-focused modules while keeping the facade and tests
stable, future work becomes easier without reopening corpus or retrieval
decisions.

## Target Module Split

### Module 1. `pilot_config.py`

Owns:

- corpus allowlist constants
- mandatory-doc constants
- canonical doc tuples
- runtime defaults
- chunking thresholds and shared regex constants

Must not own:

- query classification logic
- runtime object construction
- context-pack orchestration

### Module 2. `pilot_types.py`

Owns:

- `PreparedChunk`
- `MarkdownSection`
- `ContextDocument`
- `ContextPack`

Must remain lightweight and dependency-safe.

### Module 3. `markdown_chunks.py`

Owns:

- Markdown section parsing
- large-section splitting
- small-section collapsing
- chunk assembly
- prepared-chunk build helpers

Expected extracted functions:

- `parse_markdown_sections`
- `split_large_section`
- `collapse_small_sections`
- `chunk_markdown`
- `build_prepared_chunks`

### Module 4. `query_policy.py`

Owns:

- question classification helpers
- policy-bias path selection
- retrieval user prompt shaping
- canonical answer formatters
- raw retrieval answer shaping

Expected extracted functions:

- `is_*_question`
- `policy_bias_paths`
- `retrieval_user_prompt`
- `shape_raw_retrieval_result`
- `format_*_answer`

### Module 5. `reference_resolution.py`

Owns:

- reference normalization
- raw path extraction
- ranked-path merge logic
- fallback path resolution
- query-to-chunk scoring utilities

Expected extracted functions:

- `normalize_reference_candidate`
- `extract_reference_paths`
- `merge_ranked_paths`
- `score_chunk_for_query`
- `fallback_retrieved_paths`
- `resolve_retrieved_paths`

### Module 6. `lightrag_runtime.py`

Owns:

- runtime loading
- extraction-prompt tightening
- `LightRAG` construction
- `QueryParam` construction
- index artifact validation

Expected extracted functions:

- `_load_lightrag_runtime`
- `_tighten_entity_extraction_prompts`
- `create_rag`
- `build_query_param`
- `validate_index_artifacts`

### Module 7. `context_pack.py`

Owns:

- mandatory-doc resolution
- context-document loading
- context-pack assembly

Expected extracted functions:

- `feature_mandatory_docs`
- `mandatory_doc_paths`
- `load_context_document`
- `build_context_pack`

### Facade. `lightrag_pilot.py`

Owns only:

- public orchestration entrypoints
- CLI parsing
- compatibility imports/re-exports

Public functions to preserve:

- `build_index`
- `query_index`
- `build_parser`
- `main`

## Compatibility Rules

### Rule 1. Keep import path stable

Do not break `src.repo_memory.lightrag_pilot:main` or script consumers that
import via `lightrag_pilot`.

### Rule 2. Keep runtime defaults stable

Do not change:

- `working_dir`
- corpus allowlist
- mandatory-doc sets
- default `QueryParam` behavior
- Ollama defaults

unless a separate future feature explicitly reopens those decisions.

### Rule 3. Keep structural and behavior work separate

Do not bundle this refactor with:

- extraction cleanup
- new retrieval heuristics
- benchmark rewrites
- model changes
- rerank work

### Rule 4. Prefer test-backed moves

When moving logic across files, preserve names and coverage where practical so
the review diff stays attributable.

## Execution Phases

### Phase 1. Freeze the structural contract

Deliverables:

- canonical feature memory for the refactor
- target module split
- compatibility constraints
- explicit out-of-scope list

### Phase 2. Open isolated implementation loop

Required next step after docs/spec freeze:

- create isolated worktree/branch for `049`
- move code module-by-module
- keep facade import path stable

### Phase 3. Rewire tests and imports minimally

Expected touched product-code surface:

- `src/repo_memory/lightrag_pilot.py`
- new `src/repo_memory/*.py` helper modules
- `tests/test_lightrag_pilot.py`
- optionally `scripts/lightrag_pilot.py` only if import wiring requires it

### Phase 4. Validate no behavior drift

Validation targets:

- automated tests stay green
- current facade entrypoints still work
- benchmark semantics remain unchanged

### Phase 5. Classify follow-ups

After the refactor, classify any remaining issues as:

- structural leftovers
- extraction issues
- retrieval-quality issues
- runtime/model issues

## Touched Areas

Feature memory in main checkout:

- `specs/049-lightrag-pilot-structural-refactor/spec.md`
- `specs/049-lightrag-pilot-structural-refactor/plan.md`
- `specs/049-lightrag-pilot-structural-refactor/tasks.md`

Expected later implementation-loop surface:

- `src/repo_memory/lightrag_pilot.py`
- `src/repo_memory/pilot_config.py`
- `src/repo_memory/pilot_types.py`
- `src/repo_memory/markdown_chunks.py`
- `src/repo_memory/query_policy.py`
- `src/repo_memory/reference_resolution.py`
- `src/repo_memory/lightrag_runtime.py`
- `src/repo_memory/context_pack.py`
- `tests/test_lightrag_pilot.py`
- maybe `scripts/lightrag_pilot.py`

## Validation Plan

Success for this feature requires:

1. module split is fixed before code motion starts
2. implementation happens only through the isolated worktree/PR loop
3. the facade remains thin and public
4. current tests stay green
5. the refactor does not change benchmark results

## Risks

### R1. Hidden behavior drift during extraction

Moving answer-shaping or reference-resolution helpers can silently change
behavior if imports or shared constants move incorrectly.

### R2. Boundary regression

Without discipline, policy constants and heuristics can be split into the wrong
modules and recreate the same coupling under new filenames.

### R3. Over-bundled follow-up work

If extraction cleanup or retrieval tuning is mixed into the same PR, the review
surface becomes noisy and regression attribution weakens.

## Implementation Boundary

This feature is expected to require product-code changes, so execution must use
the standard isolated implementation loop. Main-checkout docs/specs define the
scope but do not complete the refactor.
