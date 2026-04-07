# Plan: `LightRAG` Retrieval Quality Benchmark

## Goal

Сформировать канонический benchmark, который измеряет retrieval quality шире,
чем focused precision regression в `044`, и превращает retrieval follow-ups в
data-driven roadmap.

## Baseline Inputs

Этот feature стартует из двух уже зафиксированных baseline layers:

- `042` manual usefulness review for the Phase 6 retrieval MVP
- `044` focused precision follow-up on the frozen Q3/Q4/Q5 regression set

What is already known:

- mandatory injection is stable and useful
- file-level precision required a focused fix
- policy/taxonomy answers can be improved with targeted shaping
- there is still no broad benchmark for multiple question classes and modes

Post-`046` alignment constraint:

- the benchmark must explicitly separate current-pilot rows from
  corpus-expansion rows
- `Track A` measures the current small process-memory pilot plus mandatory-doc
  policy
- `Track B` preserves broader questions that are useful, but outside the
  current pilot target set

## Benchmark Design

### Phase 1. Freeze benchmark classes

Define benchmark classes that reflect real repository-memory use cases.

Initial class set:

1. Taxonomy and read-order questions
2. Policy and pilot-boundary questions
3. Workflow and PR-loop questions
4. Feature-memory navigation questions
5. Architecture and system-location questions

### Phase 2. Freeze benchmark dataset

For each question, record:

- question text
- track
- class
- task type
- run modes
- expected canonical files
- expected key facts
- scoring notes

Dataset design rule:

- keep the dataset small enough to run manually
- keep it broad enough to expose mode-sensitive failure patterns
- retain the frozen `044` questions as one benchmark subset, not the whole set
- narrow or split mixed rows instead of scoring them against two different
  corpus contracts at once

### Phase 3. Freeze scoring rubric

Each run will be scored on a fixed 0-2 scale per dimension:

- `answer_correctness`
  - `0`: materially wrong or misleading
  - `1`: partly correct but incomplete or drifted
  - `2`: materially correct and aligned to canonical files
- `canonical_file_precision`
  - `0`: misses or invents key files
  - `1`: includes some correct files but mixed with drift/noise
  - `2`: consistently surfaces the expected canonical files
- `reference_fidelity`
  - `0`: references do not support the answer or omit key sources
  - `1`: references are partly useful but incomplete/noisy
  - `2`: references clearly support the answer and preserve key file paths
- `context_pack_usefulness`
  - `0`: pack is unsafe or insufficient for real work
  - `1`: pack is usable with manual correction
  - `2`: pack is directly useful with minimal correction

Optional analysis-only notes may also record:

- observed drift type
- missing mandatory file
- mode-specific anomaly
- answer-shaping versus ranking suspicion

### Phase 4. Freeze execution matrix

Use query-mode coverage deliberately, not exhaustively.

Initial execution guidance:

- `mix`: strongest broad baseline for cross-cutting repository questions
- `hybrid`: strong baseline for product-code and policy-sensitive work
- `local`: useful when testing local-context precision around a narrow topic
- `global`: useful when testing higher-level policy or workflow synthesis
- `naive`: optional low-baseline comparison mode for selected questions only

Initial matrix rule:

- every benchmark class must run in at least one of `mix` or `hybrid`
- at least some classes must compare against `local` or `global`
- `naive` should be sampled, not universal

Context7-backed constraints to preserve:

- official `LightRAG` docs expose `mode`, `include_references`, and
  `include_chunk_content` controls in query configuration
- the benchmark should standardize `include_references=True`
- chunk-content capture should remain optional and be used only for deeper
  debugging because it increases inspection cost

### Phase 5. Run broader baseline

Execute the frozen benchmark and record:

- per-question scores
- per-class summaries
- per-mode summaries
- cross-cutting failure patterns

### Phase 6. Convert results into follow-up priorities

Map dominant failure patterns into the next feature decision.

Decision rules:

- choose rerank-provider work only if the benchmark indicates ranking order is
  a dominant cause of failure after current answer-shaping/extraction fixes
- choose ranking-improvement work if retrieval returns relevant materials but
  ranks the wrong files too often
- choose extraction/reference work if raw answers are acceptable but references
  remain weak
- choose answer-shaping work if references are adequate but final answers still
  drift away from canonical files

## Frozen Benchmark Dataset

The canonical `045` benchmark dataset is now a split-track set:

- `Track A`: current-pilot benchmark rows
- `Track B`: corpus-expansion benchmark rows

Because `BQ3` is split into two track-specific rows, the refined dataset now
contains 11 canonical rows.

Design rules for this frozen set:

- keep the closed `044` subset as a preserved regression block
- cover all five benchmark classes at least once
- keep every class mapped to at least one of `mix` or `hybrid`
- sample `local` and `global` where they are informative
- keep `naive` out of the first baseline to avoid widening the run matrix too
  early

### Benchmark Matrix

### BQ1. Repository memory taxonomy files

- Track: `Track A`
- Class: `taxonomy-read-order`
- Question: `Which files define the repository memory taxonomy`
- Task type: `general`
- Run modes: `mix`, `hybrid`
- Expected canonical files:
  - `.specify/memory/constitution.md`
  - `AGENTS.md`
  - `docs/README.md`
  - `docs/project-idea.md`
- Expected key facts:
  - repository memory is split across `docs/`, `specs/<feature-id>/`, and
    `.specify/`
  - canonical file truth remains file-based
- Notes:
  - this preserves the frozen `044` taxonomy regression

### BQ2. Canonical read order before implementation work

- Track: `Track A`
- Class: `taxonomy-read-order`
- Question: `Which current-pilot process-memory files anchor the canonical read order before implementation work`
- Task type: `product-code`
- Run modes: `hybrid`, `global`
- Expected canonical files:
  - `AGENTS.md`
  - `.specify/memory/constitution.md`
  - `docs/README.md`
  - `docs/project-idea.md`
- Expected key facts:
  - the read order is explicitly enumerated in `AGENTS.md`
  - this row is intentionally limited to the current-pilot process-memory
    portion of that read order
  - frontend/backend docs remain conditional mandatory additions for matching
    task types rather than indexed targets for this Track A row

### BQ3A. Pilot boundary and corpus definition

- Track: `Track A`
- Class: `policy-boundary`
- Question: `Which files define the current LightRAG pilot boundary and pilot corpus policy`
- Task type: `general`
- Run modes: `mix`, `global`
- Expected canonical files:
  - `docs/context-policy.md`
  - `docs/README.md`
  - `.specify/memory/constitution.md`
  - `AGENTS.md`
- Expected key facts:
  - the pilot corpus is intentionally small and process-oriented
  - `docs/context-policy.md` defines the included and excluded corpus
  - retrieved docs are additive and subordinate to mandatory docs
- Notes:
  - this preserves the boundary/corpus-policy half of the frozen `044`
    boundary regression

### BQ3B. Local pilot setup and stack definition

- Track: `Track B`
- Class: `policy-boundary`
- Question: `Where is the local LightRAG pilot setup documented and what stack is fixed there`
- Task type: `general`
- Run modes: `mix`, `global`
- Expected canonical files:
  - `docs/lightrag-local-pilot.md`
  - `docs/context-policy.md`
- Expected key facts:
  - `docs/lightrag-local-pilot.md` fixes the local stack and script-first
    interface
  - `docs/context-policy.md` remains the canonical corpus-policy companion
- Notes:
  - this row is kept as a Track B expansion candidate because
    `docs/lightrag-local-pilot.md` is outside the current indexed pilot corpus

### BQ4. Mandatory versus retrieve-on-demand artifacts

- Track: `Track A`
- Class: `policy-boundary`
- Question: `Which artifacts are mandatory versus retrieve-on-demand for product-code work`
- Task type: `product-code`
- Run modes: `hybrid`, `mix`
- Expected canonical files:
  - `docs/context-policy.md`
  - `.specify/memory/constitution.md`
  - `AGENTS.md`
  - `docs/README.md`
  - `docs/ai-pr-workflow.md`
- Expected key facts:
  - mandatory docs are injected before product-code work
  - retrieved docs are additive and subordinate to mandatory docs
  - active feature docs are mandatory when the task is feature-scoped
- Notes:
  - this preserves the frozen `044` mandatory-vs-retrieved regression

### BQ5. Local memory mirror versus canonical memory

- Track: `Track B`
- Class: `policy-boundary`
- Question: `Which documents define local-memory mirror policy versus canonical repository memory`
- Task type: `general`
- Run modes: `mix`, `local`
- Expected canonical files:
  - `docs/context-policy.md`
  - `AGENTS.md`
  - `.specify/memory/constitution.md`
  - `docs/local-memory-sync.md`
- Expected key facts:
  - local `in_memory/memory.jsonl` is derivative rather than canonical
  - MCP/local memory does not override repository files

### BQ6. Generic PR-loop contract

- Track: `Track A`
- Class: `workflow-pr-loop`
- Question: `Which docs define the generic PR-loop contract for implementation and review`
- Task type: `review`
- Run modes: `hybrid`, `global`
- Expected canonical files:
  - `docs/ai-pr-workflow.md`
  - `AGENTS.md`
  - `.specify/memory/constitution.md`
- Expected key facts:
  - product code must go through the standard PR loop
  - required checks and AI review are part of completion

### BQ7. PR-loop completion conditions

- Track: `Track A`
- Class: `workflow-pr-loop`
- Question: `What conditions must be true before an orchestrated PR loop is considered done`
- Task type: `review`
- Run modes: `hybrid`, `mix`
- Expected canonical files:
  - `docs/ai-pr-workflow.md`
  - `AGENTS.md`
- Expected key facts:
  - green required checks
  - no blocking review findings
  - no merge conflicts
  - only human approval or final merge remaining

### BQ8. Retrieval MVP and precision follow-up ownership

- Track: `Track B`
- Class: `feature-memory-navigation`
- Question: `Which feature defined the retrieval MVP, which feature closed Q3 Q4 Q5 precision regressions, and which feature owns the broader benchmark`
- Task type: `general`
- Run modes: `mix`, `global`
- Expected canonical files:
  - `specs/042-repo-memory-platform-lightrag/spec.md`
  - `specs/042-repo-memory-platform-lightrag/evaluation.md`
  - `specs/044-lightrag-retrieval-precision/spec.md`
  - `specs/044-lightrag-retrieval-precision/evaluation.md`
  - `specs/045-retrieval-quality-benchmark/spec.md`
- Expected key facts:
  - `042` owns the retrieval MVP and initial evaluation
  - `044` owns the frozen precision follow-up
  - `045` owns broader benchmark expansion

### BQ9. Local pilot setup and stack

- Track: `Track B`
- Class: `architecture-system-location`
- Question: `Where is the local LightRAG pilot setup documented and what stack is fixed there`
- Task type: `general`
- Run modes: `mix`, `local`
- Expected canonical files:
  - `docs/lightrag-local-pilot.md`
  - `docs/context-policy.md`
- Expected key facts:
  - pilot is script-first
  - local stack uses `Ollama`, `qwen2.5:1.5b`, `nomic-embed-text`, and
    `LightRAG`
  - pilot working directory is repo-local

### BQ10. Current pilot implementation location

- Track: `Track B`
- Class: `architecture-system-location`
- Question: `Which code and tests implement the current LightRAG pilot behavior`
- Task type: `product-code`
- Run modes: `hybrid`, `local`
- Expected canonical files:
  - `src/repo_memory/lightrag_pilot.py`
  - `src/repo_memory/pilot_config.py`
  - `src/repo_memory/pilot_types.py`
  - `src/repo_memory/markdown_chunks.py`
  - `src/repo_memory/query_policy.py`
  - `src/repo_memory/reference_resolution.py`
  - `src/repo_memory/lightrag_runtime.py`
  - `src/repo_memory/context_pack.py`
  - `tests/test_lightrag_pilot.py`
  - `docs/lightrag-local-pilot.md`
  - `specs/042-repo-memory-platform-lightrag/plan.md`
- Expected key facts:
  - current pilot behavior is implemented by a thin facade plus helper modules
    under `src/repo_memory/` and the regression tests
  - implementation location is subordinate to the canonical docs/spec contract

## Frozen Execution Matrix Summary

### Track A. Current-Pilot Benchmark

- `BQ1`
- `BQ2`
- `BQ3A`
- `BQ4`
- `BQ6`
- `BQ7`

### Track B. Expansion Benchmark

- `BQ3B`
- `BQ5`
- `BQ8`
- `BQ9`
- `BQ10`

### Class/Mode Coverage

- `taxonomy-read-order`: `mix`, `hybrid`, `global`
- `policy-boundary`: `mix`, `hybrid`, `global`, `local`
- `workflow-pr-loop`: `hybrid`, `global`, `mix`
- `feature-memory-navigation`: `mix`, `global`
- `architecture-system-location`: `mix`, `local`, `hybrid`

Shared run settings for the first broader baseline:

- `include_references=True` on every benchmark query
- `include_chunk_content=False` by default
- chunk-content inspection allowed only for follow-up debugging notes
- baseline remains rerank-off by default

## Touched Areas

- `specs/045-retrieval-quality-benchmark/spec.md`
- `specs/045-retrieval-quality-benchmark/plan.md`
- `specs/045-retrieval-quality-benchmark/tasks.md`
- `specs/045-retrieval-quality-benchmark/evaluation.md` once the baseline is run

If a later implementation feature is opened from the benchmark results, that
work must use an isolated worktree/branch/PR loop before touching `src/` or
`tests/`.

## Validation Plan

Success for this feature requires:

1. the benchmark dataset is frozen in feature memory
2. the scoring rubric is explicit enough for another agent to reuse
3. the execution matrix is explicit by class and mode
4. a broader baseline run is recorded in `evaluation.md`
5. the evaluation ends with a ranked next-step recommendation

## Risks

### R1. Over-broad benchmark

If the dataset gets too large, it becomes expensive and stops being repeatable.

### R2. Ambiguous scoring

If the rubric is too loose, benchmark results become session-dependent and lose
decision value.

### R3. Premature solution bias

If the benchmark is designed to prove rerank or another favorite solution, it
stops being a useful decision tool.

### R4. Reporting without prioritization

If evaluation produces only observations and not ranked gaps, the feature does
not help choose the next engineering slice.

## Expected Follow-Up Outputs

The benchmark should let the repository choose among follow-up specs such as:

- `046-lightrag-rerank-provider`
- `047-retrieval-ranking-improvements`
- a narrower answer-shaping or reference-extraction follow-up

The next spec should be chosen only after the broader baseline is recorded.
