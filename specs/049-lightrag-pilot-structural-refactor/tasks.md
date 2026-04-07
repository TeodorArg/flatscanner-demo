# Tasks: LightRAG Pilot Structural Refactor

## Status

- [x] Feature folder created
- [x] Canonical `spec.md` created
- [x] Canonical `plan.md` created
- [x] Canonical `tasks.md` created
- [x] Canonical `evaluation.md` created

## Phase 1. Freeze Structural Contract

- [x] Define the target module decomposition for `lightrag_pilot`
- [x] Record public compatibility constraints for facade imports and CLI entrypoints
- [x] Explicitly separate structural scope from retrieval-quality, extraction, and runtime changes

## Phase 2. Open Implementation Loop

- [x] Open an isolated implementation worktree/branch/PR for `049`
- [x] Move `lightrag_pilot` logic into dedicated modules while keeping the facade stable
- [x] Re-export any required symbols for backward compatibility

## Phase 3. Validation

- [x] Run automated tests covering `lightrag_pilot` behavior
- [x] Confirm facade-level public entrypoints still work
- [x] Sync implementation-location corpus/benchmark contract after the facade split
- [x] Confirm no benchmark-result drift is introduced by the structural refactor

## Phase 4. Follow-Up Classification

- [x] Record any residual post-refactor issues as structural, extraction, retrieval-quality, or runtime/model follow-ups

## Completion Criteria

- [x] The structural target and boundaries are explicit in canonical feature memory
- [x] `src/repo_memory/lightrag_pilot.py` is reduced to a thin facade
- [x] Internal module boundaries are explicit and reviewable
- [x] Current tests remain green after the refactor
- [x] No behavior drift is introduced by the refactor itself

## Execution Note

- [x] Execute all product-code changes only through the standard isolated worktree/branch/PR loop; local main-checkout docs do not complete the feature
