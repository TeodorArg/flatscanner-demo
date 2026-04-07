# Plan: `LightRAG` Retrieval Precision Improvements

## Goal

Улучшить precision retrieval layer-а для policy/taxonomy questions, не ломая
Phase 6 MVP guarantees:

- mandatory docs остаются обязательным safeguard
- canonical files остаются source of truth
- pilot corpus остается контролируемо маленьким

## Baseline

Исходная точка зафиксирована в
`specs/042-repo-memory-platform-lightrag/evaluation.md`.

Baseline выводы:

- semantic relevance приемлема
- file-level precision нестабильна
- `retrieved_documents` extraction inconsistent
- `docs/context-policy.md` surfaced too weakly
- Q4 and Q5 are the clearest precision gaps

## Frozen Regression Set

This feature uses the following fixed regression questions from the `042`
evaluation as the precision baseline:

### Q3

Question:

- `Which files define the repository memory taxonomy`

Mode/task coverage:

- `mix`
- `general`

Expected canonical files:

- `.specify/memory/constitution.md`
- `AGENTS.md`
- `docs/README.md`
- `docs/project-idea.md`

### Q4

Question:

- `Where the local LightRAG pilot boundary and pilot corpus are defined`

Mode/task coverage:

- `mix`
- `general`

Expected canonical files:

- `docs/context-policy.md`
- `docs/README.md`
- `.specify/memory/constitution.md`
- `AGENTS.md`

### Q5

Question:

- `Which artifacts are mandatory versus retrieve-on-demand for product-code work`

Mode/task coverage:

- `hybrid`
- `product-code`

Expected canonical files:

- `docs/context-policy.md`
- `.specify/memory/constitution.md`
- `AGENTS.md`
- `docs/README.md`
- `docs/ai-pr-workflow.md`

## Implementation Strategy

### Phase 1. Freeze baseline and target questions

Сделать baseline явно воспроизводимой:

- зафиксировать Q3/Q4/Q5-style evaluation set
- сохранить expected canonical files per question
- использовать `042` evaluation как before-state

### Phase 2. Improve answer shaping

Усилить prompting и answer-shaping для policy/taxonomy questions:

- file-path-oriented wording in synthesis
- preference for canonical file names over broad directory summaries
- explicit instruction to answer with files when the question asks for files

### Phase 3. Improve structured reference extraction

Улучшить post-processing после raw `LightRAG` answer:

- extract canonical file paths more reliably
- deduplicate path variants
- prefer repository-local canonical Markdown files over abstract categories

### Phase 4. Add canonical policy-doc bias

Добавить heuristic bias toward canonical policy docs when query intent matches:

- pilot boundary
- pilot corpus
- repository memory taxonomy
- mandatory vs retrieve-on-demand policy

Primary target document:

- `docs/context-policy.md`

Supporting canonical docs:

- `.specify/memory/constitution.md`
- `AGENTS.md`
- `docs/README.md`

### Phase 5. Decide rerank behavior

Принять явное решение по rerank path.

Chosen baseline:

- disable rerank by default for the local pilot baseline

Reasoning:

- the repository currently has no configured rerank provider/model/host
- `044` is a focused precision slice, not a provider-integration feature
- warning-only rerank behavior is explicitly called out as a product gap in the
  `042` evaluation

Context7-backed constraint:

- official `LightRAG` docs state that rerank can be disabled by default with
  `RERANK_BY_DEFAULT=False`
- the same docs state that a real rerank baseline requires explicit
  `RERANK_BINDING`, `RERANK_MODEL`, `RERANK_BINDING_HOST`, and
  `RERANK_BINDING_API_KEY` configuration
- query-time rerank remains available later via `enable_rerank=True` when the
  pilot has an actual configured rerank provider

Implementation note:

- the `044` code path should set an explicit no-rerank baseline instead of
  inheriting an implicit LightRAG default
- if the Python SDK surface does not expose the API env toggle directly, the
  repository-local pilot should still make the no-rerank decision explicit in
  code and setup docs

### Phase 6. Re-run evaluation and compare

После implementation:

- re-run `hybrid` and `mix`
- compare before/after on Q3/Q4/Q5-style questions
- record where precision improved and where drift remains

## Touched Areas

- `specs/044-lightrag-retrieval-precision/`
- `src/repo_memory/lightrag_pilot.py`
- `tests/test_lightrag_pilot.py`
- optional pilot docs if rerank decision changes user-facing setup

## Validation Plan

### Regression questions

Минимальный regression set:

- which files define the repository memory taxonomy
- where the local `LightRAG` pilot boundary and pilot corpus are defined
- which artifacts are mandatory versus retrieve-on-demand for product-code work

### Success checks

Проверить, что:

- canonical files appear more often in raw answers
- `retrieved_documents` better matches raw answer
- `docs/context-policy.md` appears reliably where expected
- Q4 and Q5 show reduced drift versus baseline
- rerank behavior no longer produces an unresolved baseline warning state

## Worker Handoff

Product-code work for this feature must be implemented in an isolated
worktree/branch/PR loop, not in the main checkout.

Required code areas for the implementation worker:

- `src/repo_memory/lightrag_pilot.py`
- `tests/test_lightrag_pilot.py`

Expected implementation slices:

- file-first query shaping for policy/taxonomy questions
- deterministic post-processing for canonical path extraction/deduplication
- policy-doc bias for `docs/context-policy.md` and related canonical docs
- explicit no-rerank baseline
- regression tests covering Q3/Q4/Q5 in `hybrid` and `mix`

## Risks

### R1. Over-biasing

Слишком сильный heuristic bias может скрыть genuinely relevant supporting docs.

### R2. False precision

Можно улучшить file-path formatting without materially improving retrieval
quality.

### R3. Rerank scope creep

Попытка “быстро включить rerank” может раздуть feature beyond a focused
precision slice.

## Follow-Up Candidates

- расширить evaluation set после стабилизации Q3/Q4/Q5
- решить, нужен ли richer reference payload вместо current extracted file list
- вернуться к corpus expansion только после precision stabilization
