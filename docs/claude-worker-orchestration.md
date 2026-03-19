# Claude Worker Orchestration

This document covers only the local worker layer. The shared PR loop lives in `docs/ai-pr-workflow.md`.

## Rules

- One worker equals one task, one branch, one worktree, and one PR.
- Never run multiple Claude workers in the main checkout.
- Start each worker from current `main`.
- Keep prompts narrow and tied to one active feature folder.
- Prefer one worker by default; parallelize only independent tasks.
- Keep the soft machine-local concurrency limit at three workers unless a later ADR changes it.

## Good Parallel Splits

- isolated adapters or connectors
- tests for already-defined behavior
- docs or spec updates that do not touch the same code

Avoid parallel workers for overlapping migrations, orchestration modules, unresolved architecture, or broad refactors.

## Agent Selection

The implementation agent and the PR reviewer can be switched manually before starting a task.
The default for both is `claude`.

```powershell
# Switch both implementation agent and PR reviewer to codex
scripts/set-implementation-agent.ps1 -Agent codex

# Reset both to claude
scripts/set-implementation-agent.ps1 -Agent claude
```

`set-implementation-agent.ps1` writes the chosen agent to `.codex/implementation-agent`
(local only, gitignored) and sets the `AI_REVIEW_AGENT` GitHub repo variable.

There is no automatic failover. Re-run the script to change the selection.

## Flow

1. Codex syncs the main checkout.
2. (Optional) Run `scripts/set-implementation-agent.ps1 -Agent <claude|codex>` to choose agents.
3. Codex chooses the feature folder and task.
4. `scripts/new-claude-worktree.ps1` creates the isolated branch and worktree.
5. `scripts/start-implementation-worker.ps1` dispatches to Claude or Codex based on the agent file.
6. The implementation worker publishes with `scripts/publish-claude-branch.ps1`.
7. The resulting PR re-enters the standard `baseline-checks` / `guard` / `AI Review` loop.

## Scripts

- `scripts/new-claude-worktree.ps1`: create branch and worktree
- `scripts/set-implementation-agent.ps1`: set implementation agent and PR reviewer
- `scripts/start-implementation-worker.ps1`: dispatch to the selected implementation worker
- `scripts/start-claude-worker.ps1`: build prompt and launch Claude (called by dispatcher)
- `scripts/start-codex-worker.ps1`: build prompt and launch Codex (called by dispatcher)
- `scripts/publish-claude-branch.ps1`: push branch and open or reuse the PR
