# Claude Worker Orchestration

This document describes the local orchestration layer where Codex launches Claude Code workers through CLI on this machine.

## Purpose

Use this flow when Codex wants to delegate implementation work directly to Claude without waiting for a manual Claude session kickoff.

The model is intentionally simple:

- Codex chooses the task
- each Claude worker gets one branch and one worktree
- every worker result still lands through a pull request

## Core Rules

- One worker equals one task, one branch, one worktree, and one pull request
- Never run multiple Claude workers in the main repository checkout
- Keep prompts narrow and tied to one active feature folder
- Prefer one worker by default
- Only use parallel workers for independent tasks
- Keep the soft concurrency limit at three workers on one machine

## Recommended Split

Good candidates for parallel workers:

- isolated adapters or connectors
- Telegram formatting vs. backend normalization
- tests for already-defined behavior
- docs or spec updates that do not overlap with implementation files

Bad candidates for parallel workers:

- the same database migration chain
- the same orchestration module
- cross-cutting refactors
- architecture decisions that are still unresolved

## Standard Flow

1. Codex identifies the active feature folder and the exact task
2. Codex creates an isolated worktree with `scripts/new-claude-worktree.ps1`
3. Codex starts Claude in that worktree with `scripts/start-claude-worker.ps1`
4. Claude implements the task and may call `scripts/publish-claude-branch.ps1`
5. GitHub runs `baseline-checks`, `guard`, and `codex-review`
6. If needed, Codex triggers follow-up fixes through the existing `claude-fix` PR workflow

## Scripts

- `scripts/new-claude-worktree.ps1`
  Creates a dedicated branch plus worktree for one Claude worker
- `scripts/start-claude-worker.ps1`
  Builds a scoped worker prompt and launches Claude CLI inside the assigned worktree
- `scripts/publish-claude-branch.ps1`
  Pushes the worker branch and opens or reuses a pull request through the GitHub API

## Launch Pattern

Create a worktree:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\new-claude-worktree.ps1 `
  -FeatureFolder '001-telegram-listing-analysis-mvp' `
  -TaskSlug 'provider-detection'
```

Start a worker:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-claude-worker.ps1 `
  -FeatureFolder '001-telegram-listing-analysis-mvp' `
  -TaskId '1.1' `
  -TaskSummary 'Implement provider detection and normalized provider selection routing' `
  -WorktreePath 'C:\Users\User\FlatProject\claude-workers\codex__claude-001-telegram-listing-analysis-mvp-provider-detection'
```

Start a worker and ask Claude to publish the branch:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-claude-worker.ps1 `
  -FeatureFolder '001-telegram-listing-analysis-mvp' `
  -TaskId '1.2' `
  -TaskSummary 'Add Telegram command routing tests for supported and unsupported provider URLs' `
  -WorktreePath 'C:\Users\User\FlatProject\claude-workers\codex__claude-001-telegram-listing-analysis-mvp-routing-tests' `
  -OpenPullRequest `
  -PullRequestTitle 'Implement Telegram provider routing tests'
```

## Review And Merge

This orchestration layer does not replace the PR workflow.

All worker output still goes through:

- `baseline-checks`
- `guard`
- `codex-review`
- human approval

Codex keeps review authority even when Codex also launched the worker.
