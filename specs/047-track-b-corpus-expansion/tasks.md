# Tasks: Track B Corpus Expansion

## Status

- [x] Feature folder created
- [x] Canonical `spec.md` created
- [x] Canonical `plan.md` created
- [x] Canonical `tasks.md` created

## Phase 1. Freeze Target Set

- [x] Define the minimal `Track B` corpus allowlist
- [x] Map each allowlist entry to one or more `Track B` benchmark rows
- [x] Explicitly record nearby exclusions that remain out of corpus

## Phase 2. Canonical Policy Updates

- [x] Update `docs/context-policy.md` for the expanded corpus target
- [x] Update any companion canonical docs affected by the new corpus target
- [x] Record the final intended `Track B` corpus set in feature memory

## Phase 3. Build And Indexing Changes

- [x] Update the repo pilot build flow to use the expanded allowlist
- [x] Prevent or handle duplicate-document rebuild failures for the expanded baseline
- [x] Add or update automated coverage for corpus resolution and rebuild expectations

## Phase 4. Rebuild And Benchmark Validation

- [x] Run a clean expanded-corpus rebuild
- [x] Create `evaluation.md` for this feature
- [x] Re-run `Track B` benchmark rows (`BQ3B`, `BQ5`, `BQ8`, `BQ9`, `BQ10`)
- [x] Record per-row outcomes and residual failure classification

## Phase 5. Follow-Up Decision

- [x] Decide whether remaining gaps are ranking, rerank, extraction, answer-shaping, or further corpus-scope issues
- [x] Recommend the next feature slice from post-expansion evidence

## Completion Criteria

- [x] The expanded `Track B` target set is explicit and minimal
- [x] Canonical corpus policy and actual build inputs are aligned
- [x] A clean rebuild succeeds on the expanded baseline
- [x] `Track B` results are re-measured against the expanded corpus
- [x] Remaining failures are attributable to retrieval-quality causes rather than raw corpus mismatch

## Execution Note

- [x] Execute all product-code and runtime changes through an isolated worktree/branch/PR loop; local main-checkout docs do not complete this feature
