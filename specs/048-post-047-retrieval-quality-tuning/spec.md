# Spec: Post-047 Retrieval Quality Tuning

## Feature ID

- `048-post-047-retrieval-quality-tuning`

## Summary

Открыть следующий узкий implementation feature после `047`, который улучшает
качество retrieval на уже зафиксированном expanded baseline без смены моделей,
без `rerank`, без нового corpus scope и без больших refactor'ов chunking или
extraction.

## Problem

`047` закрыл corpus-alignment и clean rebuild для `Track B`, поэтому дальнейшие
retrieval gaps уже нельзя объяснять отсутствием нужных файлов в pilot corpus.

Следующий инженерный срез должен работать только с теми корректировками,
которые:

- не меняют `indexing/query` model choice
- не включают `rerank`
- не открывают новый corpus expansion
- не превращаются в broad cleanup extraction/chunking pipeline

После `047` репозиторию нужен отдельный feature, где residual quality issues
будут измеряться и улучшаться как:

- file-first precision
- canonical reference fidelity
- query-time retrieval shaping
- answer shaping поверх уже существующего corpus baseline

## Goal

После завершения этой фичи expanded `Track B` baseline должен давать более
детерминированные, file-first и canon-aligned ответы без изменения model stack
или corpus policy.

## Users

- orchestrator, которому нужен следующий допустимый retrieval-quality slice
- maintainer local `LightRAG` pilot-а, которому нужны улучшения без смены
  baseline stack
- implementation/review agents, которым нужна узкая и проверяемая граница
  следующего PR-loop

## Scope

В scope входит:

- query-time tuning существующих `LightRAG` параметров без смены моделей
- улучшение file-path/reference fidelity в raw retrieval answers
- deterministic answer shaping для benchmark-class questions на expanded
  baseline
- тесты и evaluation для residual precision/fidelity gaps после `047`
- явная классификация, какие проблемы решаются query/reference shaping, а какие
  остаются вне scope

Разрешённые типы изменений:

- `QueryParam` tuning:
  - `top_k`
  - `chunk_top_k`
  - token budgets
  - response formatting hints
- stronger `include_references=True` handling
- stricter extraction/use of canonical file paths from references
- narrow prompt or post-processing rules for file-first benchmark answers
- точечные preprocessing rules только если они narrowly justified конкретным
  benchmark failure и не превращаются в broad extraction cleanup

## Out Of Scope

Вне scope:

- смена generation model
- смена embedding model
- смена default query mode как новый baseline contract
- `rerank` integration or enablement
- broad chunking refactor
- broad extraction cleanup
- новый corpus scope или новая allowlist expansion
- repo-wide indexing changes

## Non-Goals

Эта фича не должна:

- переоткрывать решения `046` и `047`
- маскировать retrieval failure через новую corpus expansion
- менять pilot stack, зафиксированный в `docs/lightrag-local-pilot.md`
- превращаться в модельный эксперимент

## Core Principles

### 1. Expanded baseline stays fixed

Все улучшения должны оцениваться на corpus policy, уже зафиксированной после
`047`.

### 2. Retrieval quality must improve without model changes

Если улучшение требует смены модели или `rerank`, это отдельный будущий feature,
но не `048`.

### 3. Precision beats broadness

Нужны точечные улучшения reference fidelity и file-first answer quality, а не
новая широкая инженерная программа.

### 4. Failures must remain attributable

После `048` должно быть проще отличать:

- query-time tuning wins
- reference-extraction wins
- answer-shaping wins
- remaining out-of-scope model/extraction limitations

## Functional Requirements

### FR1. Post-047 residual gaps are frozen

Feature memory must freeze the residual benchmark questions or question classes
that remain worth tuning after `047`.

### FR2. Allowed tuning surface is explicit

The feature must explicitly state which non-model, non-rerank levers are being
used.

### FR3. File-first answer quality improves

The pilot should produce more deterministic answers that name canonical files
directly where the benchmark expects canonical file references.

### FR4. Reference fidelity improves

Retrieved references and shaped answers should better preserve exact canonical
paths and reduce false-positive or invented file mentions.

### FR5. Residual out-of-scope issues are documented

If some gaps still remain, the evaluation must state whether they now point to:

- model limits
- rerank candidates
- broader extraction work
- benchmark wording limits

## Technical Requirements

### TR1. Must preserve the current pilot stack

The feature must keep the current local stack fixed in
`docs/lightrag-local-pilot.md`.

### TR2. Must preserve the post-047 corpus policy

The feature must not expand or otherwise redefine the allowlist in
`docs/context-policy.md`.

### TR3. Must use officially available LightRAG query controls

Context7-backed LightRAG controls allowed for this feature include query
parameters such as `top_k`, `chunk_top_k`, token limits, `include_references`,
and `user_prompt`/response-shaping hooks; `enable_rerank` remains disabled and
out of scope.

### TR4. Product-code changes require the implementation loop

Any changes to `src/`, `tests/`, or `scripts/` must still land through an
isolated worktree/branch/PR loop rather than in the main checkout.

## Acceptance Criteria

### AC1. The next scope is narrow and explicit

A reader can tell exactly why `048` exists and why it is not another corpus or
model feature.

### AC2. Retrieval answers become more file-first

Evaluation shows improved canonical file naming and reference fidelity on the
chosen post-047 benchmark subset.

### AC3. Out-of-scope boundaries are preserved

No model swap, `rerank`, corpus expansion, or broad chunking/extraction refactor
is needed to complete the feature.

### AC4. The next follow-up is decision-ready

If residual gaps remain after `048`, the evaluation makes clear whether the next
feature should be model-oriented, rerank-oriented, or extraction-oriented.

## Validation

Minimum validation for this feature:

1. Freeze the post-047 residual benchmark subset.
2. Apply only allowed non-model tuning levers.
3. Re-run the chosen benchmark questions on the fixed expanded baseline.
4. Record improvements in file-first precision and reference fidelity.
5. Classify what still remains out of scope.

## References

- `specs/044-lightrag-retrieval-precision/evaluation.md`
- `specs/045-retrieval-quality-benchmark/evaluation.md`
- `specs/046-pilot-corpus-benchmark-alignment/evaluation.md`
- `specs/047-track-b-corpus-expansion/evaluation.md`
- `docs/context-policy.md`
- `docs/lightrag-local-pilot.md`
