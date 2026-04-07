# Spec: Pilot Corpus Benchmark Alignment

## Feature ID

- `046-pilot-corpus-benchmark-alignment`

## Summary

Согласовать benchmark expectations из `045` с реальной областью пилотного
`LightRAG` corpus, чтобы дальнейшие retrieval улучшения измерялись против
корректной и явно зафиксированной цели.

## Problem

`specs/045-retrieval-quality-benchmark/evaluation.md` показал, что заметная
часть провалов объясняется не ranking-only качеством, а mismatch между:

- canonical files, которые benchmark считает обязательными для ответа
- фактическим pilot corpus, который сейчас индексирует только ограниченный
  process-memory set

В результате benchmark одновременно измеряет:

- реальное retrieval quality на текущем corpus
- и скрытый corpus coverage gap

Без явного alignment decision следующий engineering slice будет смешивать
разные проблемы и давать шумные выводы.

При этом `specs/044-lightrag-retrieval-precision/evaluation.md` уже показал,
что frozen precision subset `Q3/Q4/Q5` может быть доведен до `PASS` на текущем
pilot baseline. Значит `046` не должен трактовать весь benchmark gap как
универсальную corpus problem: часть базового process/policy scope уже доказанно
работает.

## Goal

После завершения этой фичи репозиторий должен иметь канонический ответ на два
вопроса:

1. какие benchmark classes обязаны поддерживаться текущим pilot corpus
2. должен ли benchmark сузиться до current-corpus scope или pilot corpus должен
   расшириться под benchmark target set

## Users

- orchestrator, которому нужна корректная постановка следующего retrieval slice
- implementation/review agents, которым нужен ясный benchmark contract
- maintainer local `LightRAG` pilot, которому нужно понимать, что является
  corpus problem, а что ranking/answer-shaping problem

## Scope

В scope входит:

- inventory текущего pilot corpus versus `045` benchmark expectations
- classification benchmark questions into in-corpus, partially in-corpus, and
  out-of-corpus
- explicit decision framework for:
  - benchmark narrowing
  - pilot corpus expansion
  - staged hybrid approach, если это понадобится
- canonical recommendation for the next implementation slice
- validation contract for whichever alignment strategy is chosen

## Out Of Scope

Вне scope:

- немедленная product-code реализация retrieval changes в `src/` или `tests/`
- rerank-provider integration
- ranking heuristic changes as primary solution
- broad repository-wide corpus expansion without benchmark justification

## Non-Goals

Эта фича не должна:

- подменять canonical file policy retrieval-only логикой
- объявлять ranking issue решенным без corpus-alignment analysis
- менять benchmark задним числом без явного reasoned decision

## Core Principles

### 1. Benchmark and corpus must target the same contract

Если benchmark ожидает файлы вне pilot corpus, это должно быть либо допустимым
осознанным gap, либо поводом изменить corpus policy.

### 2. Canonical files remain primary

Даже при corpus expansion канонический источник истины остается в Markdown
files, а retrieval остается derivative helper.

### 3. Failures must stay attributable

После alignment должно быть можно отличить:

- corpus coverage failures
- retrieval/ranking failures
- answer-shaping/reference-extraction failures

### 4. Product-code changes require a separate implementation loop

Если alignment decision приведет к изменению `src/`, `tests/`, indexing scripts,
или реального pilot build flow, это должно идти через isolated worktree/branch/PR
loop, а не через main checkout.

## Functional Requirements

### FR1. Corpus-versus-benchmark inventory

Feature must record which canonical files are:

- already included in the current pilot corpus
- referenced by the benchmark but currently excluded
- needed only for specific benchmark classes

### FR2. Benchmark-class alignment map

Feature must map each frozen `045` benchmark question or class to one of:

- aligned with current corpus
- partially aligned
- misaligned

This mapping must explicitly preserve the `044`-validated subset as the known
aligned baseline unless new evidence contradicts it.

### FR3. Explicit alignment decision

Feature must end with a canonical decision for the immediate next direction:

- narrow the benchmark to current corpus
- expand the pilot corpus to match benchmark targets
- or split the benchmark into current-corpus and expanded-corpus tracks

### FR4. Follow-up implementation trigger

If the chosen strategy requires product-code or indexing changes, the feature
must state that a separate implementation loop is required before touching
`src/` or `tests/`.

## Technical Requirements

### TR1. Must use 045 benchmark as the input baseline

The alignment analysis must start from the frozen dataset and results in
`specs/045-retrieval-quality-benchmark/`.

### TR2. Must respect current context policy

Any recommendation must remain consistent with `docs/context-policy.md` unless
the feature explicitly proposes a canonical policy update.

### TR3. Must separate doc-policy changes from code changes

Doc/spec decisions may be recorded directly in this feature. Code changes must
be deferred to an implementation feature/worktree loop.

## Acceptance Criteria

### AC1. Alignment state is explicit

A reader can tell which benchmark classes are valid for the current corpus and
which are not.

### AC2. Next step is decision-ready

The feature ends with a concrete recommendation that distinguishes corpus
alignment work from retrieval-quality work.

### AC3. Follow-up execution boundary is clear

If corpus expansion or indexing changes are needed, the spec states that they
must happen in a separate implementation loop.

## Validation

Minimum validation for this feature:

1. Compare the current pilot corpus policy against the frozen `045` benchmark.
2. Reconcile that comparison with the `044` evaluation so already-closed
   `Q3/Q4/Q5` precision work is not misclassified as a new corpus gap.
3. Classify benchmark failures by likely cause.
4. Record the preferred alignment strategy and why it outranks alternatives.
5. State whether a follow-up implementation feature is required.

## References

- `specs/045-retrieval-quality-benchmark/spec.md`
- `specs/045-retrieval-quality-benchmark/plan.md`
- `specs/045-retrieval-quality-benchmark/evaluation.md`
- `specs/044-lightrag-retrieval-precision/evaluation.md`
- `docs/context-policy.md`
- `docs/lightrag-local-pilot.md`
