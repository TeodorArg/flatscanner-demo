# Tasks: `LightRAG` Retrieval Precision Improvements

## Status

- [x] Feature folder created
- [x] Canonical `spec.md` created
- [x] Canonical `plan.md` created
- [x] Canonical `tasks.md` created

## Phase 1. Baseline

- [ ] Import evaluation baseline from `042`
- [ ] Fix regression question set for Q3/Q4/Q5-style queries
- [ ] Define expected canonical files per regression question

## Phase 2. Prompting And Answer Shaping

- [ ] Implement file-path-oriented prompting for policy/taxonomy questions
- [ ] Prefer file-level answers when the query explicitly asks for files
- [ ] Reduce concept-first and directory-first answer drift

## Phase 3. Reference Extraction

- [ ] Implement structured reference-extraction improvements
- [ ] Deduplicate path variants and preserve canonical repository paths
- [ ] Improve `retrieved_documents` alignment with raw answer

## Phase 4. Canonical Policy Bias

- [ ] Add heuristic bias toward `docs/context-policy.md`
- [ ] Add heuristic support for constitution/AGENTS/docs-readme policy docs
- [ ] Verify policy-doc bias does not hide relevant supporting files

## Phase 5. Rerank Decision

- [ ] Decide whether baseline rerank is disabled or configured
- [ ] Implement the chosen rerank behavior in the pilot path
- [ ] Document the rerank decision if user-facing setup changes

## Phase 6. Regression Validation

- [ ] Add regression tests for Q3/Q4/Q5-style questions
- [ ] Re-run evaluation set in `hybrid`
- [ ] Re-run evaluation set in `mix`
- [ ] Record before/after comparison versus `042`

## Completion Criteria

- [ ] Policy/taxonomy queries return canonical files more consistently
- [ ] `retrieved_documents` better matches raw answer
- [ ] Q4 and Q5 no longer show the same visible drift as `042`
- [ ] Rerank behavior is explicit and no longer left in warning-only baseline
