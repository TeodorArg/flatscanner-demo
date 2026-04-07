# Phase 7 Evaluation: Repo-Memory Platform with `LightRAG`

## Scope

This note records the manual usefulness review for the Phase 6 retrieval MVP.

Evaluation date:

- 2026-04-07

Validated interface:

- `uv run python scripts/lightrag_pilot.py build --clean`
- `uv run python scripts/lightrag_pilot.py context-pack ...`

Observed baseline:

- pilot indexing completed successfully on the fixed corpus
- mandatory documents were injected consistently
- final context packs stayed usable even when ranked retrieval was imperfect

## Questions Run

### Q1. What must be read before changing the orchestration or delivery flow

- Mode: `hybrid`
- Task type: `product-code`
- Verdict: `PASS`

Notes:

- mandatory injection worked
- semantic answer was relevant
- structured `retrieved_documents` was weaker than the raw answer

### Q2. Which documents constrain the review and merge loop

- Mode: `hybrid`
- Task type: `review`
- Verdict: `PASS`

Notes:

- mandatory injection worked
- retrieval returned relevant review-loop documents
- structured references were acceptable, though not perfectly minimal

### Q3. Which files define the repository memory taxonomy

- Mode: `mix`
- Task type: `general`
- Verdict: `PARTIAL`

Notes:

- mandatory injection worked
- semantic answer was useful
- answer drifted toward directories and concepts instead of canonical file paths
- final pack remained usable because the mandatory layer contained the right files

### Q4. Where the local `LightRAG` pilot boundary and pilot corpus are defined

- Mode: `mix`
- Task type: `general`
- Verdict: `PARTIAL`

Notes:

- raw answer correctly pointed to `docs/context-policy.md`
- structured `retrieved_documents` did not reliably preserve that canonical file
- supporting process documents were still relevant

### Q5. Which artifacts are mandatory versus retrieve-on-demand for product-code work

- Mode: `hybrid`
- Task type: `product-code`
- Verdict: `PARTIAL`

Notes:

- mandatory injection worked
- semantic precision was the weakest of the five questions
- raw answer mixed mandatory and retrieve-on-demand artifacts
- answer drifted toward broad categories instead of canonical policy files

## Overall Assessment

### What worked

- policy-driven mandatory injection is stable
- pilot retrieval is useful as a semantic helper
- final context packs are generally usable for human review
- the MVP proves that retrieval can assist repository-memory navigation without
  replacing canonical files

### Main gaps

- file-level precision is weaker than semantic relevance
- structured `retrieved_documents` extraction is inconsistent
- policy and taxonomy questions tend to produce concept-first answers instead of
  file-first answers
- `docs/context-policy.md` is not consistently surfaced in the structured
  retrieved set
- the policy question about mandatory versus retrieve-on-demand artifacts still
  shows semantic drift

## Comparison With Full Manual Read Order

- pilot retrieval reduces reading load for broad process questions
- manual read order is still more reliable for exact policy and taxonomy
  questions
- current MVP is good enough for assisted context assembly, but not yet strong
  enough to replace manual file selection for precision-sensitive policy work

## Follow-Up Path

Recommended next improvement slice:

- strengthen file-path-oriented retrieval answers
- improve structured reference extraction from raw LightRAG answers
- bias policy and taxonomy queries toward canonical files such as
  `docs/context-policy.md`
- decide whether rerank should remain enabled without a configured rerank model
- keep the pilot corpus small until policy-question precision improves

Recommended repository action:

- keep this evaluation in feature memory
- implement retrieval-precision improvements in a separate branch or follow-up
  feature slice, rather than folding more scope into the Phase 6 MVP
