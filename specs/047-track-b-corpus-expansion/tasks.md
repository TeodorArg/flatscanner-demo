# Tasks: Track B Corpus Expansion

## Status

- [x] Feature folder created
- [x] Canonical `spec.md` created
- [x] Canonical `plan.md` created
- [x] Canonical `tasks.md` created

## Phase 1. Freeze Target Set

- [ ] Define the minimal `Track B` corpus allowlist
- [ ] Map each allowlist entry to one or more `Track B` benchmark rows
- [ ] Explicitly record nearby exclusions that remain out of corpus

## Phase 2. Canonical Policy Updates

- [ ] Update `docs/context-policy.md` for the expanded corpus target
- [ ] Update any companion canonical docs affected by the new corpus target
- [ ] Record the final intended `Track B` corpus set in feature memory

## Phase 3. Build And Indexing Changes

- [ ] Update the repo pilot build flow to use the expanded allowlist
- [ ] Prevent or handle duplicate-document rebuild failures for the expanded baseline
- [ ] Add or update automated coverage for corpus resolution and rebuild expectations

## Phase 4. Rebuild And Benchmark Validation

- [ ] Run a clean expanded-corpus rebuild
- [ ] Create `evaluation.md` for this feature
- [ ] Re-run `Track B` benchmark rows (`BQ3B`, `BQ5`, `BQ8`, `BQ9`, `BQ10`)
- [ ] Record per-row outcomes and residual failure classification

## Phase 5. Follow-Up Decision

- [ ] Decide whether remaining gaps are ranking, rerank, extraction, answer-shaping, or further corpus-scope issues
- [ ] Recommend the next feature slice from post-expansion evidence

## Completion Criteria

- [ ] The expanded `Track B` target set is explicit and minimal
- [ ] Canonical corpus policy and actual build inputs are aligned
- [ ] A clean rebuild succeeds on the expanded baseline
- [ ] `Track B` results are re-measured against the expanded corpus
- [ ] Remaining failures are attributable to retrieval-quality causes rather than raw corpus mismatch

## Execution Note

- [ ] Execute all product-code and runtime changes through an isolated worktree/branch/PR loop; local main-checkout docs do not complete this feature
