# AGENTS.md

This repository uses `github/spec-kit` with two memory layers:

- `docs/` for durable product and architecture context
- `specs/<feature-id>/` for feature intent, plan, and execution state

## Read Order

1. `.specify/memory/constitution.md`
2. `docs/README.md`
3. `docs/project-idea.md`
4. `docs/project/frontend/frontend-docs.md`
5. `docs/project/backend/backend-docs.md`
6. `docs/adr/*.md`
7. `specs/*/spec.md`
8. `specs/*/plan.md`
9. `specs/*/tasks.md`
10. Relevant implementation files

## Roles

- Codex owns architecture, review quality, CI/CD health, and local Claude orchestration.
- Claude Code is the primary implementation agent for product code.

## Boundaries

- Codex may directly edit docs, ADRs, specs, prompts, workflows, templates, and other process files.
- Product code in `src/`, `tests/`, and runtime setup should normally land through Claude-authored pull requests.
- Multi-agent work must use isolated git worktrees; never run multiple coding agents in one working tree.

## Working Rules

- Start every task from current `main`.
- Keep changes scoped and avoid unrelated refactors.
- Update docs or specs before code when behavior or architecture changes.
- Keep one branch and one PR per Claude worker task.
- Treat `docs/`, `specs/`, and `.specify/` as repository memory, not session memory.
- Keep `.github/workflows/` green.
- Automated PR review is selected only through the repo variable `AI_REVIEW_AGENT`.

## Completion

At task completion:

1. Update `specs/<feature-id>/tasks.md`.
2. Record durable decisions in `docs/` or `docs/adr/` when needed.
3. Capture follow-up work in the same feature folder or a new spec.

An orchestrated PR loop is finished only when the current PR head SHA has:

- no blocking review findings
- green required checks
- no merge conflicts
- only human approval or final merge remaining

If any of those are false, the task is still in progress unless the user explicitly pauses it.
