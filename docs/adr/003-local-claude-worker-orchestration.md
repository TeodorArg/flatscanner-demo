# ADR 003: Local Claude Worker Orchestration

## Status

Accepted

## Context

Codex needed a safe way to launch local Claude implementation work without giving up the existing PR-based merge path.

## Decision

- Codex may launch Claude locally for approved scoped tasks.
- Each Claude worker must use its own branch and git worktree.
- Each worker branch maps to exactly one pull request.
- Codex remains the dispatcher, reviewer, and merge gate owner.
- Default mode is one worker; parallel workers are allowed only for independent tasks.
- The default soft concurrency limit is three workers on one machine.

## Consequences

- Local parallel implementation becomes possible without shared-working-tree conflicts.
- PR creation, AI review, and merge gates stay unchanged.
- Parallel work still requires operator judgment for file overlap and architecture risk.
