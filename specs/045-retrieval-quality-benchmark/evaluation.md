# Evaluation: `LightRAG` Retrieval Quality Benchmark

## Purpose

This document is the canonical execution sheet for the broader `045`
retrieval-quality benchmark.

It freezes:

- the benchmark run protocol
- the scorecard format
- the question list to execute
- the summary structure for turning results into follow-up priorities

This file should be updated as the broader baseline is run. Until then, the
question set and scorecard format are considered frozen, while the actual
results remain pending.

## Evaluation Status

- Date created: `2026-04-07`
- Baseline status: `COMPLETED`
- Baseline run date: `2026-04-07`
- Based on:
  - `specs/042-repo-memory-platform-lightrag/evaluation.md`
  - `specs/044-lightrag-retrieval-precision/evaluation.md`
- Run note:
  - benchmark queries completed successfully against the current existing
    `.lightrag/index`
  - an attempted `build` refresh failed on duplicate-document validation for
    the pilot corpus, so this benchmark reflects query behavior on the existing
    index rather than a clean rebuilt index

## Run Protocol

### Standard Query Settings

Use these defaults unless a benchmark row explicitly requires something else:

- `include_references=True`
- `include_chunk_content=False`
- rerank disabled in the current baseline
- use the repository-local pilot entrypoint and current fixed pilot corpus

Context7-backed runbook constraints:

- official `LightRAG` supports `naive`, `local`, `global`, `hybrid`, and `mix`
  modes
- official `LightRAG` supports references in query responses when
  `include_references=True`
- chunk content can be included for deeper inspection, but only when
  references are enabled

### Scoring Rubric

Score each dimension on a `0-2` scale.

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

### Verdict Mapping

- `PASS`: all dimensions materially strong, with no blocking drift for the
  question goal
- `PARTIAL`: useful but with visible drift, noise, or missing support
- `FAIL`: materially unreliable for the intended use

## Frozen Benchmark Questions

## BQ1. Repository memory taxonomy files

- Class: `taxonomy-read-order`
- Task type: `general`
- Modes: `mix`, `hybrid`
- Question: `Which files define the repository memory taxonomy`
- Expected canonical files:
  - `.specify/memory/constitution.md`
  - `AGENTS.md`
  - `docs/README.md`
  - `docs/project-idea.md`
- Expected key facts:
  - repository memory is split across `docs/`, `specs/<feature-id>/`, and
    `.specify/`

### Result

- Verdict: `PASS`
- Notes:
  - `mix` and `hybrid` both produced the correct canonical file list in the raw
    answer
  - `hybrid` still retrieved extra process docs (`README_PROCESS_RU.md`,
    `PROCESS_OVERVIEW_EN.md`), so reference fidelity is not perfectly minimal

### Scores

- `answer_correctness`: `2`
- `canonical_file_precision`: `2`
- `reference_fidelity`: `1`
- `context_pack_usefulness`: `2`

## BQ2. Canonical read order before implementation work

- Class: `taxonomy-read-order`
- Task type: `product-code`
- Modes: `hybrid`, `global`
- Question: `What is the canonical read order before implementation work`
- Expected canonical files:
  - `AGENTS.md`
  - `.specify/memory/constitution.md`
  - `docs/README.md`
  - `docs/project-idea.md`
  - `docs/project/frontend/frontend-docs.md`
  - `docs/project/backend/backend-docs.md`
- Expected key facts:
  - the read order is explicitly enumerated in `AGENTS.md`

### Result

- Verdict: `PARTIAL`
- Notes:
  - both `hybrid` and `global` answered with a plausible workflow sequence
  - neither mode actually surfaced the expected read-order files from
    `AGENTS.md`; retrieval drifted into broad process docs and omitted the
    frontend/backend docs expected by the frozen benchmark

### Scores

- `answer_correctness`: `1`
- `canonical_file_precision`: `1`
- `reference_fidelity`: `0`
- `context_pack_usefulness`: `1`

## BQ3. Pilot boundary and corpus definition

- Class: `policy-boundary`
- Task type: `general`
- Modes: `mix`, `global`
- Question: `Where the local LightRAG pilot boundary and pilot corpus are defined`
- Expected canonical files:
  - `docs/context-policy.md`
  - `docs/lightrag-local-pilot.md`
  - `docs/README.md`
  - `AGENTS.md`
- Expected key facts:
  - `docs/context-policy.md` defines the pilot corpus boundary
  - `docs/lightrag-local-pilot.md` defines stack and pilot interface

### Result

- Verdict: `PARTIAL`
- Notes:
  - `mix` correctly centered the answer on `docs/context-policy.md`
  - `global` named `docs/context-policy.md` but still claimed the boundary was
    not explicitly defined and invented a possible workflow file
  - neither mode surfaced `docs/lightrag-local-pilot.md`, so the stack/setup
    half of the question remains under-supported

### Scores

- `answer_correctness`: `1`
- `canonical_file_precision`: `1`
- `reference_fidelity`: `1`
- `context_pack_usefulness`: `1`

## BQ4. Mandatory versus retrieve-on-demand artifacts

- Class: `policy-boundary`
- Task type: `product-code`
- Modes: `hybrid`, `mix`
- Question: `Which artifacts are mandatory versus retrieve-on-demand for product-code work`
- Expected canonical files:
  - `docs/context-policy.md`
  - `.specify/memory/constitution.md`
  - `AGENTS.md`
  - `docs/README.md`
  - `docs/ai-pr-workflow.md`
- Expected key facts:
  - mandatory docs are injected before product-code work
  - retrieved docs are additive and subordinate to mandatory docs

### Result

- Verdict: `PASS`
- Notes:
  - both `hybrid` and `mix` produced the intended file-first answer
  - `docs/context-policy.md` was consistently retrieved and the mandatory set
    was correctly represented in final documents
  - this remains the strongest broader-benchmark question after the `044`
    follow-up

### Scores

- `answer_correctness`: `2`
- `canonical_file_precision`: `2`
- `reference_fidelity`: `2`
- `context_pack_usefulness`: `2`

## BQ5. Local memory mirror versus canonical memory

- Class: `policy-boundary`
- Task type: `general`
- Modes: `mix`, `local`
- Question: `Which documents define local-memory mirror policy versus canonical repository memory`
- Expected canonical files:
  - `docs/context-policy.md`
  - `AGENTS.md`
  - `.specify/memory/constitution.md`
  - `docs/local-memory-sync.md`
- Expected key facts:
  - local `in_memory/memory.jsonl` is derivative
  - canonical repository files remain primary

### Result

- Verdict: `FAIL`
- Notes:
  - both `mix` and `local` answered with the wrong documents
  - the run failed to surface `docs/local-memory-sync.md` or
    `docs/context-policy.md` as the defining canonical pair
  - answers drifted into `docs/project-idea.md`, `README_PROCESS_RU.md`, and
    `DELIVERY_FLOW_RU.md`, which do not define the mirror-policy boundary

### Scores

- `answer_correctness`: `0`
- `canonical_file_precision`: `0`
- `reference_fidelity`: `0`
- `context_pack_usefulness`: `0`

## BQ6. Generic PR-loop contract

- Class: `workflow-pr-loop`
- Task type: `review`
- Modes: `hybrid`, `global`
- Question: `Which docs define the generic PR-loop contract for implementation and review`
- Expected canonical files:
  - `docs/ai-pr-workflow.md`
  - `AGENTS.md`
  - `.specify/memory/constitution.md`
- Expected key facts:
  - product code must go through the standard PR loop
  - required checks and AI review are part of the contract

### Result

- Verdict: `PARTIAL`
- Notes:
  - both modes produced a usable PR-loop answer shape
  - however, the retrieval layer preferred `README_PROCESS_RU.md`,
    `DELIVERY_FLOW_RU.md`, and `docs/project-idea.md` over the actual canonical
    contract file `docs/ai-pr-workflow.md`
  - the final pack stayed usable because `docs/ai-pr-workflow.md` was injected
    as mandatory for review work

### Scores

- `answer_correctness`: `1`
- `canonical_file_precision`: `1`
- `reference_fidelity`: `0`
- `context_pack_usefulness`: `1`

## BQ7. PR-loop completion conditions

- Class: `workflow-pr-loop`
- Task type: `review`
- Modes: `hybrid`, `mix`
- Question: `What conditions must be true before an orchestrated PR loop is considered done`
- Expected canonical files:
  - `docs/ai-pr-workflow.md`
  - `AGENTS.md`
- Expected key facts:
  - green required checks
  - no blocking findings
  - no merge conflicts
  - only human approval or final merge remaining

### Result

- Verdict: `PARTIAL`
- Notes:
  - `mix` produced the complete rule set including human approval/final merge
  - `hybrid` omitted the final human-approval condition
  - both modes retrieved broad process docs rather than the exact canonical PR
    contract source, so the answer is useful but not file-precise

### Scores

- `answer_correctness`: `2`
- `canonical_file_precision`: `1`
- `reference_fidelity`: `0`
- `context_pack_usefulness`: `1`

## BQ8. Retrieval MVP and precision follow-up ownership

- Class: `feature-memory-navigation`
- Task type: `general`
- Modes: `mix`, `global`
- Question: `Which feature defined the retrieval MVP, which feature closed Q3 Q4 Q5 precision regressions, and which feature owns the broader benchmark`
- Expected canonical files:
  - `specs/042-repo-memory-platform-lightrag/spec.md`
  - `specs/042-repo-memory-platform-lightrag/evaluation.md`
  - `specs/044-lightrag-retrieval-precision/spec.md`
  - `specs/044-lightrag-retrieval-precision/evaluation.md`
  - `specs/045-retrieval-quality-benchmark/spec.md`
- Expected key facts:
  - `042` owns the retrieval MVP
  - `044` owns the frozen precision follow-up
  - `045` owns broader benchmark expansion

### Result

- Verdict: `FAIL`
- Notes:
  - both `mix` and `global` failed to name the actual feature files from
    `042`, `044`, and `045`
  - answers drifted into abstract discussion about MVPs and regressions instead
    of pointing to canonical feature-memory artifacts
  - no spec or evaluation file from the expected feature set appeared in
    retrieved or final documents

### Scores

- `answer_correctness`: `0`
- `canonical_file_precision`: `0`
- `reference_fidelity`: `0`
- `context_pack_usefulness`: `0`

## BQ9. Local pilot setup and stack

- Class: `architecture-system-location`
- Task type: `general`
- Modes: `mix`, `local`
- Question: `Where is the local LightRAG pilot setup documented and what stack is fixed there`
- Expected canonical files:
  - `docs/lightrag-local-pilot.md`
  - `docs/context-policy.md`
- Expected key facts:
  - pilot is script-first
  - local stack uses `Ollama`, `qwen2.5:1.5b`, `nomic-embed-text`, and
    `LightRAG`

### Result

- Verdict: `PARTIAL`
- Notes:
  - `mix` named `lightrag-local-pilot.md` correctly but did not recover the
    fixed stack in enough detail
  - `local` was materially wrong and claimed the setup lives in `docs/README.md`
  - neither mode retrieved `docs/lightrag-local-pilot.md` into the final pack

### Scores

- `answer_correctness`: `1`
- `canonical_file_precision`: `0`
- `reference_fidelity`: `0`
- `context_pack_usefulness`: `1`

## BQ10. Current pilot implementation location

- Class: `architecture-system-location`
- Task type: `product-code`
- Modes: `hybrid`, `local`
- Question: `Which code and tests implement the current LightRAG pilot behavior`
- Expected canonical files:
  - `src/repo_memory/lightrag_pilot.py`
  - `tests/test_lightrag_pilot.py`
  - `docs/lightrag-local-pilot.md`
  - `specs/042-repo-memory-platform-lightrag/plan.md`
- Expected key facts:
  - current pilot behavior is implemented in the pilot module and its tests

### Result

- Verdict: `FAIL`
- Notes:
  - both `hybrid` and `local` missed `src/repo_memory/lightrag_pilot.py` and
    `tests/test_lightrag_pilot.py`
  - answers drifted into generic process language and did not identify the
    actual implementation locations
  - this is the clearest product-code-location failure in the broader benchmark

### Scores

- `answer_correctness`: `0`
- `canonical_file_precision`: `0`
- `reference_fidelity`: `0`
- `context_pack_usefulness`: `0`

## Summary Template

### By Question Class

- `taxonomy-read-order`: `PARTIAL`
  - BQ1 passes cleanly, but BQ2 still drifts from canonical read-order files
- `policy-boundary`: `PARTIAL`
  - BQ4 is strong and BQ3 is usable, but BQ5 fails on local-memory mirror
    policy
- `workflow-pr-loop`: `PARTIAL`
  - answers are often semantically usable, but references prefer broad process
    docs over `docs/ai-pr-workflow.md`
- `feature-memory-navigation`: `FAIL`
  - retrieval does not yet navigate active historical feature memory reliably
- `architecture-system-location`: `FAIL`
  - setup and implementation-location questions remain weak, especially when
    code/test paths are required

### By Query Mode

- `mix`: `PARTIAL`
  - strongest overall mode in this benchmark; good on taxonomy and
    mandatory-vs-retrieved policy, but still weak on feature-memory navigation
    and local-memory policy
- `hybrid`: `PARTIAL`
  - strong on product-code mandatory policy, weaker on read-order and code/test
    implementation-location questions
- `global`: `PARTIAL`
  - acceptable for broad workflow framing, but too brittle for pilot-boundary
    and feature-memory ownership questions
- `local`: `FAIL`
  - weakest mode in this benchmark; repeatedly misses setup/policy/code-location
    targets and often collapses to generic nearby process docs

### Dominant Failure Patterns

- retrieval is much stronger on policy questions when `docs/context-policy.md`
  is already a favored canonical target
- feature-memory navigation across `specs/042`, `specs/044`, and `specs/045`
  fails almost completely because the current pilot corpus does not contain
  active feature-memory files
- setup and implementation-location questions fail because the current pilot
  corpus excludes `src/`, `tests/`, and `docs/lightrag-local-pilot.md` from the
  indexed set, so answers drift into adjacent process docs
- review/workflow questions are semantically usable but references still prefer
  broad process guides instead of the exact canonical contract file
- `local` mode is materially weaker than `mix` and `hybrid` for this repo's
  current process-memory-only corpus

### Ranked Follow-Up Gaps

1. Corpus-boundary mismatch for benchmark classes that expect
   `docs/lightrag-local-pilot.md`, `docs/local-memory-sync.md`, active feature
   specs, or implementation files. The current pilot corpus is too narrow for
   these questions.
2. Retrieval still over-prefers broad process docs (`README_PROCESS_RU.md`,
   `PROCESS_OVERVIEW_EN.md`, `DELIVERY_FLOW_RU.md`) when the question asks for a
   more specific canonical contract.
3. `local` mode underperforms enough on this corpus that it should not be
   treated as a strong default for repo-memory question answering.

### Recommended Next Feature

- `046-pilot-corpus-benchmark-alignment`
  - first decide whether the benchmark should narrow to current-corpus-only
    questions or the pilot corpus should expand to include the canonical files
    now required by `045`
  - rerank-provider work is not yet justified as the immediate next step,
    because the dominant failures look corpus-boundary-driven rather than
    ranking-only
