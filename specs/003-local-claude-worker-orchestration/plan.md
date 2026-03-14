# Implementation Plan: Local Claude Worker Orchestration

## Summary

Add a lightweight orchestration layer where Codex can launch Claude CLI locally in isolated git worktrees, while keeping PR creation, GitHub checks, and Codex review as the durable delivery path.

## Files And Areas

- `AGENTS.md` and `CLAUDE.md` for updated orchestration and isolation rules
- `docs/adr/003-local-claude-worker-orchestration.md` for the durable decision
- `docs/claude-worker-orchestration.md` for the operator runbook
- `docs/ai-pr-workflow.md` and `docs/project/backend/backend-docs.md` for workflow integration
- `.github/claude/prompts/implementation-worker.md` for reusable worker instructions
- `scripts/new-claude-worktree.ps1` for branch and worktree creation
- `scripts/start-claude-worker.ps1` for prompt generation and local Claude launch
- `scripts/publish-claude-branch.ps1` for push and PR creation
- `specs/003-local-claude-worker-orchestration/` for execution tracking

## Proposed Workflow

1. Codex selects a task from the active feature folder
2. Codex creates a dedicated worker worktree and branch
3. Codex launches Claude CLI in that worktree with a narrow prompt
4. Claude implements the task, validates it, and commits locally
5. Claude or Codex publishes the branch to GitHub and opens or reuses a PR
6. Existing `baseline-checks`, `guard`, `codex-review`, and human approval remain unchanged

## Risks

- Running too many workers at once can still create indirect merge pressure
- Ambiguous task boundaries can cause branch overlap even with worktrees
- PR creation depends on local GitHub credentials being available on the machine

## Validation

- PowerShell parser accepts the new scripts
- A temporary worktree can be created from the script
- The worker launcher can generate a prompt without starting Claude when `-PromptOnly` is used
- The publish script supports a safe `-WhatIf` dry run
