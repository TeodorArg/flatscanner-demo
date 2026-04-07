# Evaluation: `LightRAG` Retrieval Precision Improvements

## Scope

This note records the post-implementation evaluation for
`044-lightrag-retrieval-precision`.

Evaluation date:

- 2026-04-07

Validated interface:

- `uv run --extra repo_memory python scripts/lightrag_pilot.py build`
- `uv run --extra repo_memory python scripts/lightrag_pilot.py context-pack ...`

Comparison baseline:

- `specs/042-repo-memory-platform-lightrag/evaluation.md`

## Questions Run

### Q3. Which files define the repository memory taxonomy

- Modes: `hybrid`, `mix`
- Initial verdict: `PARTIAL`

Observed behavior:

- mandatory injection stayed stable in both modes
- `mix` retrieved `docs/project-idea.md`, which is one of the expected
  canonical files
- `hybrid` retrieved process overview documents that are relevant, but not the
  strongest file-first answer for taxonomy
- raw answers still drifted:
  - `hybrid` named `docs/context-policy.md` plus process overview docs instead
    of focusing on the frozen canonical taxonomy set
  - `mix` hallucinated `docs/memory.md`, which is not a canonical file in this
    repository

## Q3 Follow-Up Result

Follow-up scope:

- `Q3 taxonomy-file precision`

Follow-up evaluation date:

- 2026-04-07

Follow-up validation:

- `uv run --extra dev pytest tests/test_lightrag_pilot.py`
- `uv run --extra repo_memory python scripts/lightrag_pilot.py context-pack "Which files define the repository memory taxonomy" --mode hybrid`
- `uv run --extra repo_memory python scripts/lightrag_pilot.py context-pack "Which files define the repository memory taxonomy" --mode mix`

Observed result after the follow-up implementation:

- Q3 raw answer is now deterministic and file-first in both `hybrid` and `mix`
- Q3 names the frozen canonical taxonomy files explicitly:
  - `.specify/memory/constitution.md`
  - `AGENTS.md`
  - `docs/README.md`
  - `docs/project-idea.md`
- Q3 no longer emits invented or non-canonical file names in raw answers
- Q3 final context pack remains aligned with the mandatory process docs while
  the answer itself stays focused on the frozen taxonomy file set

Updated assessment:

- Q3 is now `PASS`

### Q4. Where the local `LightRAG` pilot boundary and pilot corpus are defined

- Modes: `hybrid`, `mix`
- Verdict: `PASS`

Observed behavior:

- raw answer in both modes correctly centered `docs/context-policy.md`
- `retrieved_documents` in both modes preserved `docs/context-policy.md`
- final context pack remained aligned with the expected canonical policy docs

### Q5. Which artifacts are mandatory versus retrieve-on-demand for product-code work

- Initial modes: `hybrid`, `mix`
- Initial verdict: `PARTIAL`

Initial observed behavior:

- mandatory injection worked in both modes, including feature-scoped docs and
  `docs/ai-pr-workflow.md`
- `retrieved_documents` in both modes preserved `docs/context-policy.md`
- raw answers still drifted toward broad category summaries instead of a
  canonical file-first breakdown

## Q5 Follow-Up Result

Follow-up scope:

- `Q5 policy-answer shaping`

Follow-up evaluation date:

- 2026-04-07

Follow-up validation:

- `uv run --extra dev pytest tests/test_lightrag_pilot.py`
- `uv run --extra repo_memory python scripts/lightrag_pilot.py context-pack "Which artifacts are mandatory versus retrieve-on-demand for product-code work" --mode hybrid --task-type product-code --feature-id 044-lightrag-retrieval-precision`
- `uv run --extra repo_memory python scripts/lightrag_pilot.py context-pack "Which artifacts are mandatory versus retrieve-on-demand for product-code work" --mode mix --task-type product-code --feature-id 044-lightrag-retrieval-precision`

Observed result after the follow-up implementation:

- Q5 raw answer is now file-first in both `hybrid` and `mix`
- Q5 names the mandatory product-code files explicitly:
  - `.specify/memory/constitution.md`
  - `AGENTS.md`
  - `docs/README.md`
  - `specs/044-lightrag-retrieval-precision/spec.md`
  - `specs/044-lightrag-retrieval-precision/plan.md`
  - `specs/044-lightrag-retrieval-precision/tasks.md`
  - `docs/ai-pr-workflow.md`
- Q5 also names `docs/context-policy.md` explicitly as the retrieve-on-demand
  policy source in both modes

Updated assessment:

- Q5 is now `PASS`
- the remaining open precision gap for feature `044` is Q3 taxonomy-file
  precision

## Overall Assessment

### What improved

- rerank behavior is explicit in the repository-local baseline
- Q3 now answers with the frozen canonical taxonomy files in both `hybrid` and
  `mix`
- Q4 reliably surfaces `docs/context-policy.md`
- Q5 now answers in a deterministic file-first form in both `hybrid` and `mix`

### Residual risk

- this evaluation is still bounded to the frozen Q3/Q4/Q5 regression set rather
  than a broader corpus-wide benchmark

## Verdict Against `044` Acceptance Criteria

### AC1. File-level precision improves

- `PASS`

### AC2. Structured references improve

- `PASS`

### AC3. Q4 and Q5 drift is reduced

- `PASS`

### AC4. Rerank path is explicit

- `PASS`
