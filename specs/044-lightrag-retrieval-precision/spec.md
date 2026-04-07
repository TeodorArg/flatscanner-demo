# Spec: `LightRAG` Retrieval Precision Improvements

## Feature ID

- `044-lightrag-retrieval-precision`

## Summary

Улучшить retrieval precision для repository-memory pilot-а поверх `LightRAG`,
не меняя базовую модель канонических файлов и mandatory policy.

Фокус этой фичи:

- лучшее file-level попадание для policy и taxonomy questions
- более надежное заполнение `retrieved_documents`
- явное решение по rerank behavior вместо текущего warning-driven состояния

## Problem

Phase 7 evaluation в
`specs/042-repo-memory-platform-lightrag/evaluation.md` показала, что текущий
retrieval MVP уже полезен как semantic helper, но precision на уровне
canonical files остается нестабильной.

Основные проблемы:

- raw answer модели часто полезен по смыслу, но отвечает concept-first, а не
  file-first
- structured `retrieved_documents` не всегда совпадает с raw answer
- `docs/context-policy.md` недостаточно стабильно появляется в policy-heavy
  вопросах
- вопросы Q4 и Q5 показали заметный drift на policy/taxonomy semantics
- query path оставляет rerank включенным без настроенной rerank model, из-за
  чего pilot постоянно выдает warning вместо явного product decision

## Goal

После завершения этой фичи retrieval layer должен заметно лучше выбирать и
сохранять canonical files для policy/taxonomy questions, оставаясь derivative
helper поверх file-based repository truth.

## Users

- orchestrator, которому нужен более точный context pack для policy-sensitive
  planning
- implementation and review agents, которым нужны canonical file paths, а не
  только broad semantic summaries
- разработчик, который поддерживает local `LightRAG` pilot и хочет уменьшить
  ручную донастройку контекста

## Scope

В scope входит:

- file-path-oriented prompting для policy/taxonomy queries
- улучшение structured reference extraction из raw `LightRAG` answer
- усиление приоритета canonical policy files, особенно `docs/context-policy.md`
- явное решение по rerank behavior:
  - либо отключить default rerank path
  - либо реально настроить rerank provider/model и зафиксировать это
- regression validation на вопросах класса Q3/Q4/Q5 из `042` evaluation

## Out Of Scope

Вне scope:

- расширение pilot corpus beyond current controlled boundary
- переход на production API deployment
- перестройка всей retrieval architecture
- graph-ontology enrichment
- замена Markdown canonical files любым retrieval-first storage

## Non-Goals

Эта фича не должна:

- менять mandatory-doc policy как основной safeguard
- подменять manual read order для всех precision-sensitive задач
- расширять scope до полной semantic-answer optimization
- превращаться в широкий refactor всего `LightRAG` pilot layer

## Core Principles

### 1. Canonical files remain primary

Precision improvement должна усиливать выбор canonical files, а не ослаблять
роль repository files как source of truth.

### 2. Policy questions should prefer policy files

Вопросы про taxonomy, pilot boundary и mandatory-vs-retrieved policy должны
смещаться в сторону canonical policy docs, а не broad conceptual summaries.

### 3. Structured outputs matter

`retrieved_documents` должны лучше отражать то, что реально использовалось в
raw answer и final context pack.

### 4. Rerank behavior must be explicit

Если rerank остается в системе, он должен быть либо корректно настроен, либо
явно выключен в baseline, чтобы pilot не жил в warning-only состоянии.

## Functional Requirements

### FR1. File-first answers for policy/taxonomy questions

Для policy/taxonomy class queries retrieval flow должен чаще возвращать
canonical file paths, а не только directory-level или concept-level summaries.

### FR2. Better structured reference extraction

`retrieved_documents` должны надежнее извлекаться из raw answer и лучше
совпадать с canonical files, упомянутыми в synthesis step.

### FR3. Canonical policy-doc bias

Для вопросов про pilot boundary, pilot corpus, mandatory-vs-retrieved policy и
repository memory taxonomy должна существовать явная bias strategy в пользу:

- `docs/context-policy.md`
- `.specify/memory/constitution.md`
- `AGENTS.md`
- `docs/README.md`

### FR4. Stable handling of Q4 and Q5

Вопросы класса:

- where the local `LightRAG` pilot boundary and pilot corpus are defined
- which artifacts are mandatory versus retrieve-on-demand for product-code work

не должны давать заметный semantic drift относительно canonical policy files.

### FR5. Rerank decision recorded

В этой фиче должно быть зафиксировано одно из решений:

- baseline disables rerank by default
- baseline configures a working rerank provider/model and documents it

Current implementation decision for the local pilot baseline:

- rerank is disabled by default
- query-time rerank remains a future opt-in only after a real rerank provider is
  configured and documented

## Technical Requirements

### TR1. Baseline must reference 042 evaluation

Новая validation baseline должна явно использовать результаты из
`specs/042-repo-memory-platform-lightrag/evaluation.md`.

### TR2. Post-processing may use heuristics

Precision improvement может использовать repository-local heuristics после raw
`LightRAG` answer, если они deterministic и объяснимы.

### TR3. Query-mode coverage stays explicit

Изменения должны быть проверены как минимум в `hybrid` и `mix` modes.

### TR4. Rerank behavior must match docs

Если baseline выбирает disable path, это должно соответствовать documented
`LightRAG` behavior. По документации `LightRAG`, rerank можно отключить через
`RERANK_BY_DEFAULT=False`; иначе требуется explicit rerank configuration.

## Acceptance Criteria

### AC1. File-level precision improves

Policy/taxonomy queries чаще и стабильнее возвращают canonical files.

### AC2. Structured references improve

`retrieved_documents` лучше совпадает с canonical files, отраженными в raw
answer и final context pack.

### AC3. Q4 and Q5 drift is reduced

Повторная evaluation показывает, что Q4 и Q5 больше не дают заметный drift по
сравнению с baseline `042`.

### AC4. Rerank path is explicit

Warning-only rerank state больше не остается неявным baseline behavior.

## Validation

Минимальная validation для этой фичи:

1. Зафиксировать baseline из `042` evaluation.
2. Прогнать regression set на Q3/Q4/Q5-style questions.
3. Сравнить raw answer, `retrieved_documents`, and final context pack.
4. Отдельно зафиксировать решение по rerank behavior.

Current implementation coverage added in this feature:

- automated regression coverage for Q4/Q5-style policy-bias behavior in
  `tests/test_lightrag_pilot.py`
- automated coverage for explicit no-rerank query-param construction
- automated coverage for structured canonical path extraction and normalization

Manual follow-up still required:

- rerun the before/after evaluation set in `hybrid` and `mix`
- record comparison results versus the `042` baseline

## References

- `specs/042-repo-memory-platform-lightrag/evaluation.md`
- `specs/042-repo-memory-platform-lightrag/spec.md`
- `specs/042-repo-memory-platform-lightrag/plan.md`
