# Tasks: Post-047 Retrieval Quality Tuning

## Status

- [x] Feature folder created
- [x] Canonical `spec.md` created
- [x] Canonical `plan.md` created
- [x] Canonical `tasks.md` created
- [x] Canonical `evaluation.md` created

## Phase 1. Freeze Residual Scope

- [x] Freeze the post-047 residual benchmark subset for `048`
- [x] Define expected canonical files and reference-fidelity targets per question
- [x] Confirm that each target remains in scope without model, `rerank`, or corpus changes

## Phase 2. Select Allowed Levers

- [x] Map each target question to the smallest allowed tuning lever
- [x] Reject any candidate that implies model swap, `rerank`, corpus expansion, or broad extraction/chunking refactor
- [x] Record the final narrow implementation surface

## Phase 3. Implementation Loop

- [ ] Open an isolated implementation worktree/branch/PR for `048`
- [x] Apply non-model retrieval/reference-shaping changes in product code
- [x] Add or update automated tests for file-first precision and reference fidelity

## Phase 4. Validation

- [x] Re-run the frozen residual benchmark subset on the fixed expanded baseline
- [x] Record results in `evaluation.md`
- [x] Classify remaining failures as model, rerank, extraction/chunking, or benchmark-wording candidates

## Completion Criteria

- [x] `048` stays inside the explicit non-model scope
- [x] Retrieval answers improve in file-first precision or reference fidelity
- [x] The next follow-up direction is clearer after evaluation

## Execution Note

- [ ] Execute product-code changes only through the standard isolated worktree/branch/PR loop; local main-checkout doc edits do not complete the feature
