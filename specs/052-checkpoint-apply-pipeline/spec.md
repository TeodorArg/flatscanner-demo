# Spec: Checkpoint Apply Pipeline

## Feature ID

- `052-checkpoint-apply-pipeline`

## Summary

Открыть следующую implementation feature после `051`, которая переводит
checkpoint decision из read-only classification в controlled apply flow:

- автоматически запускает checkpoint decision helper после canonical
  doc/spec/task updates
- интерпретирует outcome как apply plan
- условно выполняет downstream steps для:
  - `LightRAG`
  - MCP memory
  - local `in_memory/memory.jsonl`

без превращения derivative layers в новый source of truth.

## Problem

Feature `051` закрывает только decision layer:

- helper уже умеет вернуть `neither`, `lightrag_only`, `mcp_local_only`, or
  `both`
- process docs и task templates уже требуют прогонять helper до финализации
  commit/PR state

Но после classification по-прежнему остается ручной operational gap:

- кто и как выполняет `LightRAG` refresh/rebuild validation
- кто и как обновляет MCP memory
- кто и как refresh-ит local `in_memory/memory.jsonl`
- как это сделать reproducible before commit without hiding risky side effects

Нужен следующий узкий слой, который не переоткрывает architecture discussion,
а operationalizes the already-fixed checkpoint workflow.

## Goal

После завершения этой фичи репозиторий должен иметь controlled apply pipeline,
который:

1. запускает checkpoint decision helper как standard pre-finalization step
2. получает decision + reasoning + parity hint
3. строит apply plan для `LightRAG`, MCP, and local mirror
4. выполняет only the in-scope downstream steps for the returned outcome
5. оставляет explainable trace в task/PR workflow

## Users

- orchestrator, которому нужен repeatable before-commit checkpoint apply flow
- implementation agent, которому нужен one-path command instead of manual
  branching
- maintainer repo-memory platform, которому нужно уменьшить operational drift
  between feature branches and durable repository memory layers

## Scope

В scope входит:

- repository-local apply command or pipeline entrypoint
- automatic invocation of `scripts/checkpoint_decision.py decide` as the first
  classification step
- outcome-driven apply flow for:
  - `LightRAG` refresh/rebuild validation when the outcome requires it
  - MCP memory update when the outcome requires it
  - local `in_memory/memory.jsonl` refresh only when parity is useful
- explainable apply summary for the branch checkpoint
- task/PR-loop alignment so the apply step is part of the standard flow before
  commit/PR finalization
- tests for representative apply scenarios and safety boundaries

## Out Of Scope

- changing the canonical context-economy architecture
- replacing Markdown files as source of truth
- implicit background automation that mutates state without an explicit apply
  step
- broad repo-wide `LightRAG` redesign
- CI comment publishing or GitHub-only automation as the primary interface

## Non-Goals

This feature must not:

- skip canonical file updates and infer durable facts from git diff alone
- make `memory.jsonl` a trigger source instead of a derivative target
- hide expensive or destructive operations behind opaque defaults
- force MCP/local sync for every feature regardless of checkpoint outcome

## Core Principles

### 1. Decide first, then apply

`051` remains the classification layer. `052` consumes that result; it does not
replace the helper with new duplicated policy logic.

### 2. Files stay canonical

Apply work happens only after canonical doc/spec/task updates already exist.

### 3. Side effects stay explicit

The pipeline may automate execution, but it must remain obvious which steps are
running for `LightRAG`, MCP, and local mirror.

### 4. Outcomes stay conditional

`LightRAG`, MCP, and local mirror do not all run on every checkpoint. The
decision outcome must control which apply steps happen.

## Functional Requirements

### FR1. The pipeline runs checkpoint classification automatically

After canonical doc/spec/task updates and before finalizing commit/PR state, the
pipeline must run `scripts/checkpoint_decision.py decide` for the current branch
state.

### FR2. The pipeline maps every decision to an apply plan

For the helper decision:

- `neither`
- `lightrag_only`
- `mcp_local_only`
- `both`

the pipeline must determine which downstream actions are required and which are
skipped.

### FR3. The pipeline can apply `LightRAG` work when required

If the outcome is `lightrag_only` or `both`, the pipeline must run the
repository-approved `LightRAG` refresh/rebuild validation path.

### FR4. The pipeline can apply MCP memory work when required

If the outcome is `mcp_local_only` or `both`, the pipeline must support
updating MCP memory for durable repo-scoped facts already present in canonical
files.

### FR5. The pipeline can refresh local mirror conditionally

If local parity is recommended, the pipeline must support refreshing
`in_memory/memory.jsonl`; otherwise it must skip that step cleanly.

### FR6. The pipeline reports what it did

The pipeline output must make clear:

- which checkpoint decision was returned
- which downstream actions ran
- which downstream actions were skipped
- whether manual follow-up is still required

## Technical Requirements

### TR1. Product-code changes still require the standard implementation loop

Any apply pipeline implementation under `scripts/`, `src/`, or `tests/` must
land through the standard isolated worktree/branch/PR loop.

### TR2. The pipeline should reuse the decision helper

The apply layer should call the `051` helper or its shared module contract
rather than reimplementing classification rules independently.

### TR3. Write order must remain canonical

The pipeline must preserve:

1. canonical files first
2. `LightRAG` validation when required
3. MCP memory when required
4. local mirror refresh when useful

### TR4. Validation must cover mixed apply cases

The feature should validate at least:

- `neither` skips all apply steps
- `lightrag_only` runs only the `LightRAG` path
- `mcp_local_only` runs MCP and optionally local parity work
- `both` runs both classes in the correct order

## Acceptance Criteria

### AC1. The post-classification flow is reproducible

Another agent can follow one standard command or pipeline path instead of
manually branching after reading the helper output.

### AC2. The apply flow respects the decision outcome

The pipeline runs only the downstream steps implied by the checkpoint outcome.

### AC3. Canonical ordering is preserved

The automation does not treat MCP or local mirror as source of truth and does
not run before canonical files are updated.

### AC4. The feature stays operationally narrow

The feature solves checkpoint apply execution without reopening broader retrieval
or memory architecture decisions.

## Validation

Minimum validation for this feature:

1. Freeze the standard apply flow after `051` classification.
2. Freeze the command/interface for the apply layer.
3. Validate outcome-specific apply behavior with automated tests.
4. Confirm canonical ordering is preserved.
5. Confirm skipped actions are reported clearly.

## References

- `docs/context-economy-workflow.md`
- `docs/context-policy.md`
- `docs/local-memory-sync.md`
- `docs/ai-pr-workflow.md`
- `specs/051-checkpoint-decision-helper/spec.md`
- `specs/051-checkpoint-decision-helper/plan.md`
