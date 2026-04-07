# Spec: Checkpoint Decision Helper

## Feature ID

- `051-checkpoint-decision-helper`

## Summary

Открыть узкую implementation feature для read-only helper, который
автоматизирует canonical checkpoint decision из `docs/context-economy-workflow.md`
и выдает одно из решений:

- `neither`
- `LightRAG only`
- `MCP/local sync only`
- `both`

без создания нового source of truth и без автоматического применения изменений в
v1.

## Problem

Feature `050` уже зафиксировала:

- layered context-economy architecture
- budget profiles
- retrieval trigger matrix
- explicit checkpoint checklist

Но пока решение по checkpoint still requires manual interpretation of the
workflow doc.

Это создает практическую проблему:

- ежедневный workflow все еще требует ручного сравнения нескольких trigger rules
- decisions могут быть неравномерными между агентами и сессиями
- один и тот же тип изменения может приводить к разным manual outcomes

Нужен минимальный helper, который будет читать текущий canonical policy и
состояние репозитория и выдавать explainable recommendation.

## Goal

После завершения этой фичи репозиторий должен иметь read-only helper, который:

1. анализирует candidate checkpoint inputs
2. определяет, затронута ли индексируемая `LightRAG` truth layer
3. определяет, появились ли новые durable repo-scoped facts
4. выдает canonical action recommendation
5. объясняет reasoning по шагам

## Users

- orchestrator, которому нужен быстрый и повторяемый checkpoint decision
- implementation/review agent, которому нужен explainable answer before sync or
  rebuild work
- maintainer repo-memory platform, которому нужно уменьшить manual process
  overhead

## Scope

В scope входит:

- repository-local read-only helper command
- input modes such as:
  - explicit changed file paths
  - current repo diff or git-based changed-file discovery
- policy-aware classification against:
  - indexed corpus allowlist
  - durable-fact triggers
  - local-parity rules
- final decision enum:
  - `neither`
  - `lightrag_only`
  - `mcp_local_only`
  - `both`
- human-readable reasoning output
- tests for representative decision scenarios

## Out Of Scope

- automatically rebuilding `LightRAG`
- automatically writing MCP memory
- automatically rewriting `in_memory/memory.jsonl`
- changing the canonical context-economy workflow itself
- broad retrieval or memory-architecture redesign

## Non-Goals

This feature must not:

- replace canonical docs with tool-owned logic
- invent durable facts not present in canonical files
- silently mutate repository state in v1
- treat git diff alone as canonical truth without checking policy context

## Core Principles

### 1. Read-only first

The first helper version should recommend actions, not execute them.

### 2. Canon drives logic

The helper must follow the policy fixed in:

- `docs/context-economy-workflow.md`
- `docs/context-policy.md`
- `docs/local-memory-sync.md`

### 3. Explainability matters

The helper output must make clear why the result is `neither`, `LightRAG only`,
`MCP/local sync only`, or `both`.

### 4. Narrow implementation surface

This feature should automate only the checkpoint decision, not the whole
context-economy workflow.

## Functional Requirements

### FR1. Helper returns one canonical decision

For a given checkpoint input, the helper must return exactly one of:

- `neither`
- `lightrag_only`
- `mcp_local_only`
- `both`

### FR2. Helper explains the decision

Output must include the trigger reasoning, such as:

- indexed corpus changed or not
- durable repo facts changed or not
- local parity useful or not

### FR3. Helper can inspect changed-file input

The helper must support at least one concrete changed-file input mechanism and
document the canonical one for the repository.

### FR4. Helper respects current allowlist policy

The helper must classify indexed-surface changes against the current explicit
allowlist in `docs/context-policy.md`, not against a hard-coded stale list.

### FR5. Helper stays read-only

The helper must not perform rebuilds or memory writes in v1.

## Technical Requirements

### TR1. Product-code changes require implementation loop

Any helper implementation under `scripts/`, `src/`, or `tests/` must land
through the standard isolated worktree/branch/PR loop.

### TR2. Canonical workflow remains primary

If helper logic and canonical docs disagree, the docs win and the helper must be
updated.

### TR3. Validation must use scenario tests

The helper should be validated against representative scenarios such as:

- only indexed corpus changed
- only durable facts changed
- both changed
- neither changed

## Acceptance Criteria

### AC1. The helper gives one stable action outcome

The same checkpoint scenario yields the same decision across runs.

### AC2. The helper is explainable

The reasoning output maps clearly to the canonical checklist.

### AC3. The helper is narrow

The helper does not perform rebuilds or sync writes automatically in v1.

### AC4. The feature is implementation-ready

The spec, plan, and tasks leave a clear isolated implementation slice.

## Validation

Minimum validation for this feature:

1. Freeze canonical helper inputs and outputs.
2. Freeze the scenario matrix.
3. Implement through an isolated worktree/PR loop.
4. Validate representative scenarios with automated tests.
5. Confirm the helper remains read-only in v1.

## References

- `docs/context-economy-workflow.md`
- `docs/context-policy.md`
- `docs/local-memory-sync.md`
- `specs/050-context-economy-workflow/spec.md`
- `specs/050-context-economy-workflow/plan.md`
