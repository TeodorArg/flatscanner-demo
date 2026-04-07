# Tasks: `LightRAG` Retrieval Quality Benchmark

## Status

- [x] Feature folder created
- [x] Canonical `spec.md` created
- [x] Canonical `plan.md` created
- [x] Canonical `tasks.md` created

## Phase 1. Benchmark Shape

- [x] Freeze benchmark question classes
- [x] Freeze benchmark dataset with question text, task type, modes, expected files, and key facts
- [x] Carry forward the frozen `044` regression subset into the broader benchmark

## Phase 2. Scoring Rubric

- [x] Define the per-dimension scoring rubric
- [x] Define verdict language and summary format
- [x] Define how mode-specific anomalies and drift types are recorded

## Phase 3. Execution Matrix

- [x] Freeze which question classes run in `mix`
- [x] Freeze which question classes run in `hybrid`
- [x] Decide where `local`, `global`, and optional `naive` comparisons are needed
- [x] Standardize reference-capture settings for benchmark runs

## Phase 4. Baseline Run

- [x] Create `evaluation.md` for the broader benchmark
- [x] Run the frozen benchmark baseline
- [x] Record per-question scores
- [x] Record per-class summaries
- [x] Record per-mode summaries

## Phase 5. Prioritization

- [x] Identify dominant failure patterns
- [x] Rank next retrieval-quality gaps by impact
- [x] Recommend the next feature slice based on benchmark evidence

## Completion Criteria

- [x] The benchmark is broader than the `044` precision slice
- [x] The rubric is reusable by another agent without hidden judgment
- [x] Baseline results are recorded in canonical feature memory
- [x] The feature ends with a ranked follow-up recommendation rather than only observations

## Execution Note

- [ ] If benchmark results lead to product-code work in `src/` or `tests/`, open a separate implementation feature and isolated worktree/branch/PR loop first
