# Feature Spec: Local Claude Worker Orchestration

## Status

Completed

## Goal

Let Codex launch local Claude workers safely without creating a second merge path.

## Resolution

- Each worker uses one branch, one worktree, and one PR.
- Codex remains dispatcher and reviewer.
- Default mode is one worker; parallel workers are allowed only for independent tasks.
- Repository-local scripts handle worktree creation, worker launch, and PR publication.

## Follow-Up

- Decide whether to automate worker queueing and concurrency caps.
- Decide whether PR creation should later move into a dedicated workflow trigger.
