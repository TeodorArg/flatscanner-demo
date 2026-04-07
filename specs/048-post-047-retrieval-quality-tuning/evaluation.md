# Evaluation: Post-047 Retrieval Quality Tuning

## Status

- Date: `2026-04-07`
- Execution status: `RESIDUAL SUBSET VALIDATED`
- Branch/worktree: `feat/048-post-047-retrieval-quality-tuning`

## Scope

This note records validation for the frozen post-`047` residual subset chosen
for feature `048`.

Validated constraints remained unchanged throughout this run:

- no generation-model change
- no embedding-model change
- no `rerank`
- no corpus expansion
- no broad chunking refactor
- no broad extraction cleanup

## Validation Run

Environment validation:

- `uv run --extra dev pytest tests/test_lightrag_pilot.py`
  - result: `30 passed`

Pilot rebuild status:

- expanded baseline build remained usable in the `048` worktree
- indexing still emits extraction-format warnings on some code/spec-heavy chunks
  during build, but these warnings did not block index finalization or the
  residual-subset query validation

Residual-subset query runs:

- `What is the canonical read order before implementation work`
  - mode: `hybrid`
  - mode: `global`
- `Which files define the current LightRAG pilot boundary and pilot corpus policy`
  - mode: `mix`
  - mode: `global`
- `Which docs define the generic PR-loop contract for implementation and review`
  - mode: `hybrid`
  - mode: `global`
- `What conditions must be true before an orchestrated PR loop is considered done`
  - mode: `mix`

## Residual Subset Results

### BQ2. Canonical read order before implementation work

- Verdict: `PASS`
- Modes checked: `hybrid`, `global`
- Observed result:
  - raw answer is now deterministic and file-first
  - answer names the intended current-pilot anchor files:
    - `AGENTS.md`
    - `.specify/memory/constitution.md`
    - `docs/README.md`
    - `docs/project-idea.md`
  - the old drift into a generic workflow sequence is no longer the primary
    answer path
- Notes:
  - `global` still retrieved `docs/project-idea.md` into the final pack, but
    the shaped answer stayed anchored to the exact canonical file list

### BQ3A. Pilot boundary and corpus definition

- Verdict: `PASS`
- Modes checked: `mix`, `global`
- Observed result:
  - after the final `048` patch, raw answer is now file-first in both modes
  - answer names the intended canonical policy set:
    - `docs/context-policy.md`
    - `.specify/memory/constitution.md`
    - `AGENTS.md`
    - `docs/README.md`
  - `docs/context-policy.md` is now the first retrieved document in both modes
  - the previous drift toward `README_PROCESS_RU.md` and
    `docs/lightrag-local-pilot.md` no longer drives the primary answer
- Notes:
  - this was the last still-open residual row from the first `048` validation
    pass and is now closed

### BQ6. Generic PR-loop contract

- Verdict: `PASS`
- Modes checked: `hybrid`, `global`
- Observed result:
  - raw answer is file-first in both modes
  - answer names the intended canonical contract files:
    - `docs/ai-pr-workflow.md`
    - `AGENTS.md`
    - `.specify/memory/constitution.md`
  - `docs/ai-pr-workflow.md` remains in mandatory docs for review work and now
    also drives the shaped answer directly

### BQ7. PR-loop completion conditions

- Verdict: `PASS`
- Modes checked: `mix`
- Observed result:
  - raw answer now explicitly includes all required completion conditions:
    - no blocking review findings
    - green required checks
    - no merge conflicts
    - only human approval or final merge remaining
  - answer is anchored to:
    - `docs/ai-pr-workflow.md`
    - `AGENTS.md`
  - the earlier omission of the final human-approval condition is no longer
    present

## Outcome Summary

### What `048` improved

- residual Track A rows from `045` are now deterministic and file-first
- reference/file-path fidelity improved for read-order, pilot-boundary, and
  PR-loop questions without changing the corpus or model stack
- review/workflow answers now anchor to `docs/ai-pr-workflow.md` instead of
  broader process overviews
- pilot-boundary answers now anchor to `docs/context-policy.md` instead of
  setup/process drift

### Remaining limits

- build-time extraction-format warnings still appear on some code/spec-heavy
  chunks, especially during entity/relation extraction
- those warnings did not block `048` acceptance, but they remain a possible
  future candidate for a separate extraction-focused feature if the repository
  decides they matter beyond current benchmark quality

## Verdict Against `048` Scope

### AC1. The next scope is narrow and explicit

- `PASS`

### AC2. Retrieval answers become more file-first

- `PASS`

### AC3. Out-of-scope boundaries are preserved

- `PASS`

### AC4. The next follow-up is decision-ready

- `PASS`

## Follow-Up Classification

Post-`048`, the frozen residual subset no longer points to an immediate
corpus-alignment gap.

If a later feature is opened, the most likely remaining categories are:

- extraction-noise cleanup for code/spec-heavy chunks
- model-quality improvements
- rerank experimentation

None of those are required to consider `048` complete.
