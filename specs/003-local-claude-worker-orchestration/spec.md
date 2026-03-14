# Feature Spec: Local Claude Worker Orchestration

## Context

The repository already supports Claude-authored pull requests and Codex review. The next step is to let Codex launch Claude CLI locally for scoped implementation tasks, including limited parallel workers, without breaking branch discipline or repository memory.

## Scope

- Add a durable orchestration model for Codex-launched Claude workers
- Document isolation rules for multi-worker execution
- Add repository-local scripts for creating worktrees, launching Claude workers, and publishing worker branches
- Keep the existing PR review and merge gates as the only integration path

## Out Of Scope

- Full autonomous merge
- Dynamic task decomposition from issues
- Cloud-hosted worker pools
- Product application code changes

## Requirements

- Every Claude worker must use an isolated git worktree and a dedicated branch
- The orchestration model must preserve the existing PR flow and Codex review loop
- The repository must provide a repeatable local script for starting a Claude worker from a scoped task
- The repository must provide a repeatable local script for publishing or reusing a PR from a worker branch
- Durable docs must explain when parallel workers are allowed and when they are not

## Acceptance Criteria

- An ADR records the local worker orchestration decision
- Durable workflow docs explain the worker model and its guardrails
- Repository scripts exist for worktree creation and worker launch
- Agent instructions reflect worktree isolation and Codex orchestration authority
- The scripts pass static PowerShell parsing and a prompt-generation validation path

## Open Questions

- Whether a future queue should limit workers automatically instead of relying on operator discipline
- Whether PR creation should later move from a local script into a dedicated GitHub workflow trigger
