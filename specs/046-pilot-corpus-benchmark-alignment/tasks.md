# Tasks: Pilot Corpus Benchmark Alignment

## Status

- [x] Feature folder created
- [x] Canonical `spec.md` created
- [x] Canonical `plan.md` created
- [x] Canonical `tasks.md` created
- [x] Canonical `evaluation.md` created

## Phase 1. Baseline Alignment Input

- [x] Freeze the current pilot corpus input set from `docs/context-policy.md`
- [x] Carry forward the `044`-validated `Q3/Q4/Q5` subset as the known aligned baseline
- [x] Freeze the expected-file matrix from `045` benchmark artifacts
- [x] Record the benchmark classes that are already well-supported versus weak

## Phase 2. Coverage Mapping

- [x] Build a per-question corpus coverage map for the frozen `045` benchmark
- [x] Classify each benchmark class as aligned, partially aligned, or misaligned
- [x] Separate likely corpus failures from ranking and answer-shaping failures

## Phase 3. Decision Analysis

- [x] Compare benchmark narrowing versus pilot corpus expansion
- [x] Evaluate whether a split benchmark track is justified
- [x] Choose the preferred alignment strategy and record the reasoning

## Phase 4. Follow-Up Boundary

- [x] State whether the preferred strategy is docs-only or requires product-code work
- [x] If product-code work is required, define the next implementation feature/worktree loop boundary
- [x] Record any durable policy updates needed outside the feature folder

## Phase 5. Sequenced Follow-Ups

- [x] Decide whether docs-only `045` refinement and `Track B` implementation expansion are separate tasks
- [x] Record docs-only `045` refinement as the first follow-up
- [x] Record `Track B` corpus/indexing expansion as a separate later implementation feature

## Completion Criteria

- [x] The current benchmark-to-corpus mismatch is explicitly mapped
- [x] The repository has a canonical recommendation for the next step
- [x] The boundary between doc/spec work and implementation work is explicit
