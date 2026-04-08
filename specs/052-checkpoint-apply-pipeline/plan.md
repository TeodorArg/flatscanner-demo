# Plan: Checkpoint Apply Pipeline

## Goal

Реализовать следующий operational layer after `051`: standard checkpoint apply
flow before commit/PR finalization.

## Strategy

Feature `051` already decides what class of action is required.

Feature `052` should not reopen classification logic. It should:

1. run the decision helper automatically
2. translate the outcome into an apply plan
3. execute only the required downstream steps
4. leave a clear trace of what ran and what was skipped

## Working Hypothesis

The remaining operational pain is not the classification itself anymore. It is
the manual branching after classification.

If the repository has one narrow apply pipeline that consumes the helper output,
then the daily loop becomes:

- update canonical files
- run one checkpoint command
- let the pipeline handle `LightRAG`, MCP, and local mirror in the correct
  order
- finalize commit/PR state

## Expected Interface

Canonical shape for v1 of the apply layer:

- repository-local command under `scripts/`
- runs the decision helper first
- prints a structured apply summary
- performs only the downstream steps required by the decision

Example summary shape:

- `decision`
- `indexed_corpus_changed`
- `durable_repo_facts_changed`
- `local_parity_recommended`
- `applied_steps`
- `skipped_steps`
- `manual_follow_up`

## Proposed Apply Flow

### Step 1. Canonical checkpoint exists

The user or agent has already updated canonical docs/spec/tasks for the current
feature branch.

### Step 2. Run decision helper

Run `scripts/checkpoint_decision.py decide --git-diff`.

### Step 3. Build apply plan from the decision

- `neither` -> skip all downstream steps
- `lightrag_only` -> run `LightRAG` validation path only
- `mcp_local_only` -> run MCP path and local parity only if recommended
- `both` -> run `LightRAG` path first, then MCP path, then local parity if
  recommended

### Step 4. Emit final apply summary

The pipeline must report exactly what happened for this checkpoint.

## Proposed Implementation Surface

Likely files:

- `scripts/` apply entrypoint
- shared `src/repo_memory/` helper module for orchestration logic
- tests for outcome-specific behavior

The implementation should reuse the `051` module instead of copying its policy
rules.

## Phase Breakdown

### Phase 1. Freeze apply contract

Deliver:

- canonical apply sequence
- outcome-to-action mapping
- write-order rules

### Phase 2. Implement repository-local apply command

Deliver:

- command entrypoint
- shared orchestration logic
- safety boundaries around side effects

### Phase 3. Validate outcome-specific behavior

Deliver:

- tests for `neither`, `lightrag_only`, `mcp_local_only`, and `both`
- branch-level example output
- confirmation that skipped steps are reported explicitly

## Risks

### R1. Silent side effects

If the apply command does too much without reporting it clearly, the workflow
becomes harder to trust than the current manual path.

### R2. Scope creep into CI-only automation

GitHub Actions can later run read-only classification on PR events and expose
results in logs or outputs, but that should remain a later integration surface
rather than the primary contract for this feature.

### R3. Wrong ordering between apply steps

If MCP/local mirror updates run before the required `LightRAG` validation or
before canonical files are stable, the pipeline will violate the context-economy
rules.

## Validation Plan

Success requires:

1. one standard apply command after canonical updates
2. reuse of the `051` decision layer
3. explicit reporting of applied versus skipped steps
4. correct ordering of `LightRAG`, MCP, and local mirror actions

## Implementation Notes

The implemented command surface is:

- `scripts/checkpoint_apply.py apply`
- shared orchestration in `src/repo_memory/checkpoint_apply.py`

The `LightRAG` validation path originally exposed duplicate-document failures on
repeated non-clean builds. The implementation now uses selective incremental
refresh in `src/repo_memory/lightrag_pilot.py`:

- unchanged indexed files are skipped
- changed indexed files are deleted and reinserted
- added indexed files are inserted
- removed indexed files are deleted
- stale duplicate doc-status artifacts are cleaned up

This keeps the apply pipeline aligned with the feature goal of controlled
checkpoint execution without falling back to full clean rebuilds on every
ordinary update.
