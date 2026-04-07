# Spec: Context-Economy Workflow

## Feature ID

- `050-context-economy-workflow`

## Summary

Зафиксировать постоянный workflow для экономии контекстного окна, в котором:

- canonical repository files остаются source of truth
- MCP memory используется как сжатый cross-session recall layer
- local `in_memory/memory.jsonl` остается selective mirror MCP
- `LightRAG` используется как retrieval accelerator только там, где manual file
  targeting уже дороже и шумнее
- context packs собираются по budget profiles, а не по принципу "прочитать все"

## Problem

После `042`-`049` в репозитории уже есть:

- canonical repository memory
- explicit mandatory-vs-retrieved policy
- local MCP mirror policy
- benchmarked `LightRAG` pilot

Но пока нет отдельного durable feature, которая фиксирует следующий
архитектурный слой:

- как именно эти memory layers должны работать вместе ради экономии токенов
- когда использовать MCP summary вместо чтения файлов
- когда retrieval оправдан, а когда он только добавляет шум
- какие budget modes должны существовать для разных типов задач

Без такого канона есть риск:

- тащить в контекст слишком много файлов "на всякий случай"
- дублировать одни и те же факты между Markdown, MCP и local mirror
- использовать `LightRAG` там, где достаточно mandatory docs и active feature
- не иметь воспроизводимого workflow для cheap session bootstrap

## Goal

После завершения этой фичи репозиторий должен иметь durable workflow, который:

1. Снижает средний размер context pack.
2. Не создает второй source of truth.
3. Разделяет roles canonical files, MCP memory, local mirror, and `LightRAG`.
4. Вводит budgeted context assembly modes для типовых задач.
5. Фиксирует, какие summaries стоит поддерживать для fast session bootstrap.

## Users

- orchestrator, которому нужно быстро собрать безопасный context pack
- implementation/review agent, которому нужен минимальный, но достаточный
  контекст
- maintainer repo-memory platform, которому нужно держать retrieval cheap and
  explainable

## Scope

В scope входит:

- durable architecture decision for layered context economy
- canonical workflow for context assembly under token budgets
- explicit rules for:
  - canonical files
  - MCP memory
  - local `memory.jsonl`
  - `LightRAG`
- definition of budget profiles such as:
  - `simple`
  - `feature-work`
  - `deep-audit`
- definition of bootstrap artifacts for cheap session start
- rules for when retrieval is allowed, required, or unnecessary
- sync-policy refinements if needed for summary-level MCP entities

## Out Of Scope

- replacing Markdown files as canonical truth
- broad repo-wide reindexing beyond already approved corpus changes
- model-stack replacement
- making local `memory.jsonl` a new retrieval backend
- shipping production automation before the workflow contract is frozen

## Non-Goals

Эта фича не должна:

- превращать MCP memory в primary design storage
- делать `LightRAG` обязательным для каждой task
- вводить "summary docs" как новый неканонический слой рядом с `docs/`
- поощрять полное чтение исторических артефактов по умолчанию

## Core Principles

### 1. Truth stays in files

Canonical repository files remain the only source of truth.

### 2. Summaries are derivative

MCP memory and local `memory.jsonl` exist to reduce repeated context load, not
to replace canonical detail.

### 3. Retrieval is conditional

`LightRAG` is used only when file discovery or ranked supporting context is
genuinely cheaper than manual targeted reads.

### 4. Context must be budgeted

Context assembly should use explicit budget profiles instead of defaulting to
maximum file inclusion.

### 5. Workflow must stay reproducible

Another agent should be able to assemble roughly the same context pack for the
same task type by following the documented policy.

## Functional Requirements

### FR1. Layer roles are explicit

The repository must define the role of:

- canonical repository files
- MCP memory
- local `in_memory/memory.jsonl`
- `LightRAG`

in one coherent workflow.

### FR2. Budget profiles are defined

The workflow must define at least these context-assembly profiles:

- `simple` for narrow factual or documentation questions
- `feature-work` for active-feature planning or implementation
- `deep-audit` for broader investigation or architecture review

Each profile must define:

- mandatory docs
- preferred summary layer
- retrieval trigger rules
- expected context size discipline

### FR3. Bootstrap summaries are defined

The workflow must define which compact facts should be available for cheap
session bootstrap, such as:

- current project identity
- active feature identity
- latest durable repo-wide decisions
- open follow-up boundaries

### FR4. Retrieval trigger rules are defined

The workflow must explicitly state when `LightRAG` is:

- unnecessary
- recommended
- required

based on question type and uncertainty.

### FR5. Sync discipline is preserved

Any new summary workflow must preserve the existing write order:

1. canonical files
2. MCP memory
3. local mirror

### FR6. Historical artifacts stay cold by default

The workflow must make clear that closed features, archives, and vendor-specific
examples are not pulled into context by default unless the task explicitly needs
them.

## Technical Requirements

### TR1. Architecture must be durable

The layered context-economy decision must be recorded as a durable architecture
decision in `docs/adr/`.

### TR2. Workflow must be canonical

The future context-economy workflow must be described in canonical repository
docs, not only in feature memory or MCP observations.

### TR3. The workflow must build on existing canon

The feature must align with:

- `docs/context-policy.md`
- `docs/local-memory-sync.md`
- `.specify/memory/constitution.md`
- `AGENTS.md`
- the `042`-`049` retrieval and memory decisions

### TR4. Metrics must be decision-ready

The feature should define a validation approach that can later compare:

- full manual read
- mandatory + MCP bootstrap
- mandatory + MCP + retrieval

for representative task classes.

## Acceptance Criteria

### AC1. The layered workflow is explicit

A reader can tell exactly when to use files, MCP memory, local mirror, and
`LightRAG`.

### AC2. Context-budget profiles are explicit

The repository defines at least `simple`, `feature-work`, and `deep-audit`
profiles.

### AC3. No new source of truth is introduced

The design keeps canonical files primary and derivative layers subordinate.

### AC4. Future implementation is scoped

The feature leaves a clear next implementation path for tooling or automation
without requiring product-code changes in the planning step itself.

## Validation

Minimum validation for this feature:

1. Freeze the layered architecture and workflow vocabulary.
2. Freeze budget-profile definitions.
3. Freeze retrieval-trigger rules.
4. Identify which durable docs must be updated or added.
5. Define the follow-up implementation surface for any automation.

## References

- `docs/context-policy.md`
- `docs/local-memory-sync.md`
- `docs/adr/000-repository-documentation-model.md`
- `specs/042-repo-memory-platform-lightrag/spec.md`
- `specs/045-retrieval-quality-benchmark/evaluation.md`
- `specs/049-lightrag-pilot-structural-refactor/spec.md`
