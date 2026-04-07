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

Вариант A:

- disable rerank in baseline if no rerank model/provider is configured

Вариант B:

- configure a real rerank provider/model and document the setup

Context7-backed constraint:

- `LightRAG` docs indicate rerank can be disabled by default with
  `RERANK_BY_DEFAULT=False`
- otherwise a provider/model/host configuration is required for rerank to be a
  real supported baseline

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
