# ADR 003: Local Claude Worker Orchestration

## Status

Accepted

## Context

The repository already supports Claude-authored pull requests and Codex review through a self-hosted runner. The team wants Codex to act as an orchestrator that can launch Claude Code locally for scoped implementation tasks and, when useful, run more than one implementation worker in parallel.

Running several coding agents in the same working tree is unsafe. It causes branch confusion, index conflicts, and hidden file overlap. The orchestration layer therefore needs a simple isolation model that stays compatible with the current PR workflow.

## Decision

Adopt a local Claude worker orchestration model with these rules:

- Codex may launch Claude Code locally through CLI for approved scoped tasks
- Every Claude worker must run in its own git worktree and its own branch
- Every worker branch must map to exactly one pull request
- Codex remains the dispatcher, reviewer, and merge gate owner
- Claude remains the implementation agent and should not merge its own work
- The default operating mode is one worker; parallelism is allowed only for independent tasks
- Keep the default parallelism limit to three concurrent Claude workers on one machine unless a future ADR changes it

## Workflow Shape

1. Codex selects a task from the active feature folder
2. Codex creates an isolated worktree from `main` or another approved base branch
3. Codex launches Claude CLI in that worktree with a narrow task prompt
4. Claude implements the task, updates relevant specs and tests, and pushes the worker branch
5. Claude opens or updates the pull request for that branch
6. GitHub Actions runs `baseline-checks`, `guard`, and `codex-review`
7. Codex reviews the PR and may trigger follow-up Claude fixes on the same branch
8. A human merges after required checks and approval

## Guardrails

- Never run two Claude workers in the same worktree
- Do not split a task across multiple workers if they are expected to touch the same files
- Prefer task-sized prompts over feature-sized prompts
- Keep orchestration scripts repository-local and auditable
- Keep PR creation and review in the existing GitHub workflow rather than inventing a second merge path

## Consequences

- The team gets higher local implementation throughput without giving up PR discipline
- Codex can act as a practical engineering manager for Claude workers
- Worktree isolation reduces accidental branch and file contention
- Parallel work must still be planned carefully; architecture-heavy changes should usually stay single-worker
