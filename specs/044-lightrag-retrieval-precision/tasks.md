# Tasks: `LightRAG` Retrieval Precision Improvements

## Status

- [x] Feature folder created
- [x] Canonical `spec.md` created
- [x] Canonical `plan.md` created
- [x] Canonical `tasks.md` created

## Phase 1. Baseline

- [x] Import evaluation baseline from `042`
- [x] Fix regression question set for Q3/Q4/Q5-style queries
- [x] Define expected canonical files per regression question

## Phase 2. Prompting And Answer Shaping

- [x] Implement file-path-oriented prompting for policy/taxonomy questions
- [x] Prefer file-level answers when the query explicitly asks for files
- [x] Reduce concept-first and directory-first answer drift

## Phase 3. Reference Extraction

- [x] Implement structured reference-extraction improvements
- [x] Deduplicate path variants and preserve canonical repository paths
- [x] Improve `retrieved_documents` alignment with raw answer

## Phase 4. Canonical Policy Bias

- [x] Add heuristic bias toward `docs/context-policy.md`
- [x] Add heuristic support for constitution/AGENTS/docs-readme policy docs
- [x] Verify policy-doc bias does not hide relevant supporting files

## Phase 5. Rerank Decision

- [x] Decide whether baseline rerank is disabled or configured
- [x] Implement the chosen rerank behavior in the pilot path
- [x] Document the rerank decision if user-facing setup changes

## Phase 6. Regression Validation

- [x] Add regression tests for Q3/Q4/Q5-style questions
- [ ] Re-run evaluation set in `hybrid`
- [ ] Re-run evaluation set in `mix`
- [ ] Record before/after comparison versus `042`

## Completion Criteria

- [ ] Policy/taxonomy queries return canonical files more consistently
- [ ] `retrieved_documents` better matches raw answer
- [ ] Q4 and Q5 no longer show the same visible drift as `042`
- [ ] Rerank behavior is explicit and no longer left in warning-only baseline

## Execution Note

- [x] Create an isolated `044` implementation worktree/branch/PR loop before editing `src/` or `tests/`
