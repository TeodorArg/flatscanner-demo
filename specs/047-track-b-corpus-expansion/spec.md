# Spec: Track B Corpus Expansion

## Feature ID

- `047-track-b-corpus-expansion`

## Summary

Открыть отдельный implementation feature для расширения `LightRAG` pilot corpus
и indexing flow под `Track B` benchmark rows, которые были явно выделены в
`045` и `046`.

Смысл этой фичи:

- не спорить больше о benchmark interpretation
- не лечить corpus-gap через answer-shaping или rerank
- а явно изменить corpus/index baseline так, чтобы `Track B` questions
  оценивались против честной целевой области

## Problem

`045` показал устойчивые провалы на `Track B` rows, а `046` зафиксировал, что
эти провалы в первую очередь объясняются не ranking-only качеством retrieval,
а тем, что нужные canonical files вообще не входят в текущий pilot corpus.

Сейчас есть ясная граница:

- `Track A` уже измеряет то, что текущий маленький process-memory pilot должен
  поддерживать
- `Track B` требует отдельного corpus/index expansion

Пока такого expansion нет:

- benchmark rows `BQ3B`, `BQ5`, `BQ8`, `BQ9`, `BQ10` остаются частично или
  полностью misaligned
- результаты broader benchmark нельзя честно интерпретировать как ranking-only
  signal
- будущие retrieval improvements risk being tuned against the wrong corpus

## Goal

После завершения этой фичи репозиторий должен иметь новый канонический
`Track B` baseline, в котором:

- pilot corpus policy расширена под целевые `Track B` files
- indexing/build flow действительно использует новый target set
- baseline rebuild выполнен на чистой целевой области
- `Track B` benchmark rows можно оценивать как retrieval-quality signal, а не
  только как corpus mismatch

## Users

- orchestrator, которому нужен честный benchmark contract для следующего
  retrieval iteration
- maintainer local `LightRAG` pilot-а, которому нужно явно управлять corpus
  boundary и rebuild workflow
- implementation/review agents, которым нужна предсказуемая связь между
  benchmark rows и реально индексируемыми canonical files

## Scope

В scope входит:

- выбор целевого `Track B` corpus set
- canonical update pilot corpus policy in `docs/context-policy.md`
- canonical sync of setup/runtime docs where the corpus target set is described
- repo pilot indexing/build flow changes needed to use the expanded corpus
- duplicate-safe or otherwise reproducible rebuild path for the expanded corpus
- validation against `Track B` benchmark rows after rebuild

Target `Track B` coverage for this feature:

- `docs/lightrag-local-pilot.md`
- `docs/local-memory-sync.md`
- selected active feature-memory files required by `BQ8`
- selected implementation-location artifacts required by `BQ10`

The exact final inclusion set must stay minimal and justified by benchmark
coverage, not by a broad "index more docs" impulse.

Frozen minimal allowlist for this feature:

- `docs/context-policy.md`
- `docs/lightrag-local-pilot.md`
- `docs/local-memory-sync.md`
- `specs/042-repo-memory-platform-lightrag/spec.md`
- `specs/042-repo-memory-platform-lightrag/plan.md`
- `specs/042-repo-memory-platform-lightrag/evaluation.md`
- `specs/044-lightrag-retrieval-precision/spec.md`
- `specs/044-lightrag-retrieval-precision/evaluation.md`
- `specs/045-retrieval-quality-benchmark/spec.md`
- `src/repo_memory/lightrag_pilot.py`
- `tests/test_lightrag_pilot.py`

Explicit nearby exclusions that remain out of corpus:

- all other `src/` files
- all other `tests/` files
- all unrelated `specs/*` files
- `docs/ai-pr-workflow.md`
- `docs/project/backend/backend-docs.md`
- `docs/project/frontend/frontend-docs.md`
- `docs/adr/*.md`

## Out Of Scope

Вне scope:

- rerank-provider integration
- ranking-only or answer-shaping-only tuning as the primary solution
- indexing the whole repository
- introducing a production retrieval service
- replacing Markdown files as canonical truth
- broad inclusion of unrelated historical specs, ADRs, or legacy domain docs

## Non-Goals

Эта фича не должна:

- размывать маленький pilot в бесконтрольный repo-wide corpus
- задним числом менять `045` or `046` decisions
- подменять mandatory-doc policy retrieval-only behavior
- трактовать accidental current index state as canonical evidence

## Core Principles

### 1. Corpus expansion must stay explicit

Каждый новый document class или path family должен быть добавлен в corpus по
явной benchmark причине.

### 2. Canonical files remain primary

Даже после expansion retrieval остается derivative helper поверх canonical
Markdown and implementation files.

### 3. Rebuild must be reproducible

Новый `Track B` baseline нельзя считать валидным без clean rebuild against the
expanded target set.

### 4. Minimal expansion beats broad expansion

Нужно индексировать минимально достаточный набор для `Track B`, а не всё подряд.

## Functional Requirements

### FR1. Expanded target set is defined

Feature memory must explicitly define which files or file groups are added to
the pilot corpus for `Track B` support.

### FR2. Corpus policy is updated canonically

`docs/context-policy.md` must be updated so the intended expanded corpus is
described in canonical repository policy rather than inferred from code.

### FR3. Build/index flow matches policy

The repo pilot build/index path must read from the same intended target set
that is documented in canonical policy.

### FR4. Track B benchmark coverage is testable

The feature must define which `Track B` rows are expected to improve after the
expansion and what files/facts count as success.

Minimum target rows:

- `BQ3B`
- `BQ5`
- `BQ8`
- `BQ9`
- `BQ10`

### FR5. Rebuild baseline is explicit

The feature must define a clean rebuild/refresh validation path for the expanded
corpus, including how duplicate-document failure is handled or prevented.

## Technical Requirements

### TR1. Must build on `045` and `046`

The feature must explicitly use:

- `specs/045-retrieval-quality-benchmark/plan.md`
- `specs/045-retrieval-quality-benchmark/evaluation.md`
- `specs/046-pilot-corpus-benchmark-alignment/evaluation.md`

### TR2. Must respect current LightRAG query/build semantics

Context7-backed constraints to preserve:

- `LightRAG` query modes remain `naive`, `local`, `global`, `hybrid`, and `mix`
- reference capture remains tied to `include_references=True`
- a changed intended corpus requires a rebuild before comparing benchmark
  outcomes as one baseline

### TR3. Product-code changes require the implementation loop

Any changes to `src/`, `tests/`, `scripts/`, or indexing/runtime setup must be
executed in an isolated worktree/branch/PR loop rather than treated as complete
from main-checkout doc edits alone.

## Acceptance Criteria

### AC1. Track B target set is no longer implicit

A reader can tell exactly which new files are part of the expanded corpus target
and why.

### AC2. Policy and implementation target the same corpus

Canonical docs and actual indexing inputs no longer drift on the intended
expanded baseline.

### AC3. Rebuild path is usable

The feature defines and validates a reproducible rebuild path for the expanded
corpus.

### AC4. Track B benchmark becomes decision-usable

After rebuild and re-run, `Track B` results can be read primarily as retrieval
quality evidence rather than raw corpus mismatch.

## Validation

Минимальная validation для этой фичи:

1. Freeze the expanded `Track B` target set.
2. Update canonical corpus-policy docs.
3. Update indexing/build inputs to match the new policy.
4. Run a clean rebuild for the expanded corpus.
5. Re-run the `Track B` benchmark rows.
6. Record which rows improved and which gaps remain ranking/retrieval issues.

## References

- `specs/045-retrieval-quality-benchmark/spec.md`
- `specs/045-retrieval-quality-benchmark/plan.md`
- `specs/045-retrieval-quality-benchmark/evaluation.md`
- `specs/046-pilot-corpus-benchmark-alignment/spec.md`
- `specs/046-pilot-corpus-benchmark-alignment/plan.md`
- `specs/046-pilot-corpus-benchmark-alignment/evaluation.md`
- `docs/context-policy.md`
- `docs/lightrag-local-pilot.md`
