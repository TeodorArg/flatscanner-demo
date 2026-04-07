# Spec: `LightRAG` Retrieval Quality Benchmark

## Feature ID

- `045-retrieval-quality-benchmark`

## Summary

Создать более широкий и воспроизводимый benchmark для retrieval quality в
repository-memory pilot-е поверх `LightRAG`, чтобы измерять не только один
узкий precision regression set, а несколько классов вопросов и их влияние на
финальный context pack.

`044` закрыл focused precision slice для frozen Q3/Q4/Q5. `045` расширяет
evaluation framework, baseline coverage и scoring rubric, чтобы дальше
принимать решения по ranking, rerank и другим retrieval improvements на данных,
а не по ощущению.

## Problem

После `044` pilot уже лучше отвечает на конкретный frozen set вопросов, но у
репозитория нет достаточно широкого benchmark-а для оценки retrieval quality
по разным question classes, task types и query modes.

Без этого сложно:

- сравнивать retrieval behavior между `naive`, `local`, `global`, `hybrid`,
  `mix`
- измерять regression beyond Q3/Q4/Q5
- различать проблемы answer correctness, file precision, reference fidelity и
  context-pack usefulness
- приоритизировать следующий engineering slice

## Goal

После завершения этой фичи у репозитория должен быть канонический benchmark,
который:

- расширяет evaluation set beyond the frozen `044` questions
- делит вопросы на явные question classes
- использует повторяемую scoring rubric
- фиксирует baseline results across selected query modes
- выдает приоритизированный список retrieval gaps для следующих feature slices

## Users

- orchestrator, которому нужен более надежный способ оценивать retrieval
  usefulness before planning work
- implementation/review agents, которым важно понимать, насколько retrieval
  реально помогает собрать correct context pack
- maintainer local `LightRAG` pilot-а, которому нужен repeatable benchmark for
  changes in retrieval behavior

## Scope

В scope входит:

- расширение benchmark question set beyond `044`
- grouping questions into explicit benchmark classes
- benchmark rubric for multiple quality dimensions
- fixed execution matrix by query mode and task type
- baseline run procedure and result-report structure
- prioritization rules for follow-up retrieval improvements

## Out Of Scope

Вне scope:

- интеграция rerank provider/model
- ranking or retrieval implementation changes in `src/`
- corpus expansion beyond the currently documented pilot boundary unless a later
  spec explicitly approves it
- production deployment changes
- replacement of Markdown files as canonical repository truth

## Non-Goals

Эта фича не должна:

- повторно открывать already-closed `044` acceptance criteria
- смешивать benchmark design с implementation of retrieval fixes
- делать benchmark depend on one-off session judgment
- превращаться в broad experimentation without durable feature memory

## Core Principles

### 1. Benchmark follows canonical file truth

Benchmark оценивает, насколько retrieval помогает находить canonical files и
собирать usable context pack, но не подменяет file-based source of truth.

### 2. Benchmark must separate quality dimensions

Нельзя смешивать:

- semantic answer usefulness
- canonical file precision
- reference fidelity
- final context-pack usefulness

Они должны оцениваться отдельно.

### 3. Benchmark must stay reproducible

Question set, query modes, task types, scoring rubric и reporting format должны
быть зафиксированы в feature memory.

### 4. Follow-up work must be data-driven

Следующие feature slices по rerank, ranking или answer shaping должны
выбираться по benchmark results, а не только по intuition.

## Functional Requirements

### FR1. Benchmark question classes defined

Feature memory must define explicit question classes such as:

- repository taxonomy and read-order questions
- policy and boundary questions
- workflow and PR-loop questions
- feature-memory navigation questions
- architecture or stack-location questions

### FR2. Frozen benchmark dataset defined

Benchmark must define a frozen question set with:

- question text
- task type
- recommended query mode coverage
- expected canonical files
- expected answer shape or key facts

### FR3. Multi-dimensional scoring rubric defined

Benchmark must score at least:

- answer correctness
- canonical file precision
- reference fidelity
- final context-pack usefulness

### FR4. Execution matrix defined

Benchmark must specify which questions are run in which `LightRAG` query modes.

Context7-backed relevance for this requirement:

- official `LightRAG` docs expose `naive`, `local`, `global`, `hybrid`, and
  `mix` query modes through `QueryParam`
- docs also expose `include_references` and optional chunk-content inclusion,
  which are relevant for judging reference fidelity and inspection depth

### FR5. Baseline report format defined

Feature memory must define how baseline results are recorded, including:

- per-question verdicts
- per-dimension scores
- summary by question class
- summary by query mode
- prioritized gap list

### FR6. Follow-up prioritization rules defined

Benchmark results must map cleanly to possible next specs, including:

- rerank-provider work only if benchmark results justify it
- ranking improvements only if ranking is the dominant failure mode
- answer-shaping or extraction follow-up only if benchmark isolates those gaps

## Technical Requirements

### TR1. Must build on `042` and `044`

The benchmark must explicitly reference:

- `specs/042-repo-memory-platform-lightrag/evaluation.md`
- `specs/044-lightrag-retrieval-precision/evaluation.md`

### TR2. Reference capture must stay explicit

Runs must use `include_references=True` so benchmark scoring can inspect the
reference payload, and may optionally record chunk content when deeper analysis
is needed.

### TR3. Query-mode coverage must be deliberate

Not every question must run in every mode, but the benchmark must state why a
mode is included or excluded for each question class.

### TR4. Rerank stays a benchmark dimension, not an implementation task

`045` may record a future comparison axis for rerank-off baseline versus
later rerank-on scenarios, but it must not implement rerank integration.

## Acceptance Criteria

### AC1. Benchmark scope is broader than `044`

The feature defines a benchmark that covers multiple question classes beyond the
frozen Q3/Q4/Q5 precision slice.

### AC2. Scoring is repeatable

Another agent can run the documented benchmark and record results using the same
rubric and report format.

### AC3. Baseline reveals prioritized gaps

The benchmark output produces a ranked set of next retrieval-quality problems
rather than a flat list of observations.

### AC4. Follow-up paths are explicit

The feature leaves a clear decision path for whether the next investment should
be rerank, ranking, extraction, answer shaping, or some other retrieval change.

## Validation

Минимальная validation для этой фичи:

1. Freeze benchmark classes and dataset.
2. Freeze the scoring rubric and execution matrix.
3. Run the broader benchmark baseline.
4. Record per-question and per-dimension results.
5. Produce a prioritized follow-up list tied to actual observed failures.

## References

- `specs/042-repo-memory-platform-lightrag/evaluation.md`
- `specs/044-lightrag-retrieval-precision/spec.md`
- `specs/044-lightrag-retrieval-precision/plan.md`
- `specs/044-lightrag-retrieval-precision/evaluation.md`
