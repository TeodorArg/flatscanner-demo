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

## Flow

1. Codex syncs the main checkout.
2. Codex chooses the feature folder and task.
3. `scripts/new-claude-worktree.ps1` creates the isolated branch and worktree.
4. `scripts/start-claude-worker.ps1` launches Claude with a scoped prompt.
5. Claude implements and may publish with `scripts/publish-claude-branch.ps1`.
6. The resulting PR re-enters the standard `baseline-checks` / `guard` / `AI Review` loop.

## Scripts

- `scripts/new-claude-worktree.ps1`: create branch and worktree
- `scripts/start-claude-worker.ps1`: build prompt and launch Claude
- `scripts/publish-claude-branch.ps1`: push branch and open or reuse the PR
