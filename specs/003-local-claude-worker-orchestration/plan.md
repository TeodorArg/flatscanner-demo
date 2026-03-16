# Implementation Plan: Local Claude Worker Orchestration

## Summary

Add repository-local scripts and runbooks so Codex can create isolated worktrees, launch Claude with scoped prompts, and publish the result into the standard PR loop.

## Touched Areas

- worker scripts and prompt template
- `docs/claude-worker-orchestration.md`
- `docs/ai-pr-workflow.md`
- `docs/adr/003-local-claude-worker-orchestration.md`

## Validation Completed

- PowerShell parser checks
- worktree creation and prompt generation
- publish dry-run
- end-to-end worker launch to reviewed PR
