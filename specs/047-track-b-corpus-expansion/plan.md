# Plan: Track B Corpus Expansion

## Goal

Расширить текущий `LightRAG` pilot corpus и indexing baseline ровно настолько,
чтобы `Track B` benchmark rows из `045` стали честной retrieval target set.

## Baseline Inputs

Этот feature стартует из уже зафиксированных решений:

- `044` доказал, что узкий policy/taxonomy subset можно довести до хорошего
  precision without broad corpus expansion
- `045` показал, что broader benchmark rows падают неравномерно и что biggest
  failures cluster around out-of-corpus targets
- `046` explicitly split the benchmark into `Track A` and `Track B`, and
  decided that `Track B` needs a separate implementation feature

## Problem Framing

Current pilot corpus by canonical policy includes only a small process-memory
set and deliberately excludes several files needed by `Track B`:

- `docs/lightrag-local-pilot.md`
- `docs/local-memory-sync.md`
- active feature-memory docs
- `src/`
- `tests/`

As a result:

- `BQ3B` and `BQ9` cannot fairly succeed on setup/stack questions
- `BQ5` cannot fairly succeed on local-memory mirror policy
- `BQ8` cannot fairly succeed on feature-memory ownership/history
- `BQ10` cannot fairly succeed on implementation-location questions

## Expansion Strategy

### Phase 1. Freeze the minimal Track B target set

Choose the smallest justified expansion that covers the current `Track B` rows.

Initial target candidates:

1. `docs/lightrag-local-pilot.md`
2. `docs/local-memory-sync.md`
3. selected `specs/042`, `specs/044`, `specs/045` spec/evaluation files needed
   by `BQ8`
4. selected implementation files for `BQ10`:
   - `src/repo_memory/lightrag_pilot.py`
   - `src/repo_memory/pilot_config.py`
   - `src/repo_memory/pilot_types.py`
   - `src/repo_memory/markdown_chunks.py`
   - `src/repo_memory/query_policy.py`
   - `src/repo_memory/reference_resolution.py`
   - `src/repo_memory/lightrag_runtime.py`
   - `src/repo_memory/context_pack.py`
   - `tests/test_lightrag_pilot.py`
   - possibly `specs/042-repo-memory-platform-lightrag/plan.md` if still needed
     as supporting canonical context

Selection rule:

- include only files with a direct benchmark justification
- prefer explicit allowlist entries over broad directory-wide inclusion when
  possible

Frozen allowlist for implementation:

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

Row mapping for this allowlist:

- `BQ3B`: `docs/lightrag-local-pilot.md`, `docs/context-policy.md`
- `BQ5`: `docs/local-memory-sync.md`, `docs/context-policy.md`
- `BQ8`: selected `specs/042`, `specs/044`, `specs/045` files
- `BQ9`: `docs/lightrag-local-pilot.md`, `docs/context-policy.md`
- `BQ10`: thin facade plus helper implementation modules under `src/repo_memory/`,
  `tests/test_lightrag_pilot.py`, `docs/lightrag-local-pilot.md`,
  `specs/042-repo-memory-platform-lightrag/plan.md`

Explicit exclusions kept outside the pilot:

- all other `src/` and `tests/` files
- all other `specs/*` files
- `docs/ai-pr-workflow.md`
- backend/frontend stack docs
- ADRs and vendor-specific examples

### Phase 2. Canonical policy sync

Update the durable docs that define corpus expectations.

Primary canonical target:

- `docs/context-policy.md`

Likely companion targets:

- `docs/lightrag-local-pilot.md`
- `specs/047-track-b-corpus-expansion/spec.md`
- `specs/047-track-b-corpus-expansion/tasks.md`

Policy sync must answer:

- which new paths are now included in the pilot corpus
- which nearby paths remain excluded
- whether the pilot is still called "small" and in what qualified sense

### Phase 3. Index/build flow changes

Change the repo-local pilot build path so the actual indexing inputs match the
new policy.

Touched implementation areas are likely:

- `scripts/lightrag_pilot.py`
- `src/repo_memory/lightrag_pilot.py`
- `tests/test_lightrag_pilot.py`

Required behavior:

- build input resolution must reflect the expanded allowlist
- duplicate-document handling must no longer block a clean rebuild on the
  canonical expanded target set
- logs or debug output should still make the resolved corpus inspectable

### Phase 4. Clean rebuild and validation

Run the expanded-corpus rebuild as one clean baseline, then re-run the `Track B`
benchmark rows.

Required validation set:

- `BQ3B`
- `BQ5`
- `BQ8`
- `BQ9`
- `BQ10`

Scoring goal:

- failures should now be attributable mainly to retrieval/ranking/reference
  behavior, not raw out-of-corpus mismatch

### Phase 5. Record residual gaps

If some `Track B` rows still fail after expansion, classify the remainder:

- ranking issue
- reference extraction issue
- answer-shaping issue
- benchmark wording issue
- still-missing corpus target

This phase determines whether the next slice should be rerank, ranking,
extraction, or another narrower corpus follow-up.

## Touched Areas

Docs/spec layer:

- `docs/context-policy.md`
- `docs/lightrag-local-pilot.md`
- `specs/047-track-b-corpus-expansion/spec.md`
- `specs/047-track-b-corpus-expansion/plan.md`
- `specs/047-track-b-corpus-expansion/tasks.md`
- `specs/047-track-b-corpus-expansion/evaluation.md`

Implementation layer expected for the later PR loop:

- `scripts/lightrag_pilot.py`
- `src/repo_memory/lightrag_pilot.py`
- `tests/test_lightrag_pilot.py`

## Validation Plan

Success for this feature requires:

1. a minimal explicit Track B allowlist is frozen
2. canonical policy docs match that allowlist
3. the build flow uses the same target set
4. an expanded-corpus rebuild completes reproducibly
5. `Track B` benchmark rows are re-run and recorded in a new evaluation

## Risks

### R1. Over-expansion

The feature could accidentally turn into broad repository indexing. The plan
must resist that and keep a minimal allowlist.

### R2. Policy/implementation drift

Docs may say one thing while build inputs index something else. Validation must
compare both.

### R3. Duplicate-document rebuild failures

The rebuild path already showed duplicate-document problems in `045`, so this
feature must not assume rebuild reliability without explicit handling.

### R4. False success through accidental index state

A cached or stale `.lightrag/index` must not be mistaken for a clean expanded
baseline.

## Implementation Boundary

This feature is expected to lead to product-code changes, so execution must use
the standard isolated implementation loop:

1. open an implementation worktree from current `main`
2. land runtime/indexing/test changes on one scoped branch
3. run required checks
4. review results against the expanded `Track B` benchmark

Main-checkout docs alone do not complete this feature.

## Expected Output

At the end of this feature, the repository should know:

- what the expanded `Track B` corpus actually is
- whether the expanded rebuild is stable
- which `Track B` rows now pass
- which remaining failures are true retrieval-quality follow-ups
