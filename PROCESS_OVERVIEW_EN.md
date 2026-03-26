# flatscanner: process overview

## What this repository demonstrates

`flatscanner` is both:

- a Telegram-based rental listing analysis service
- a demonstration repository for a spec-driven, AI-assisted development workflow

The repo is designed to show how work moves from a user request to a merged
pull request through explicit repository memory, isolated implementation
workers, CI, and AI review.

## Core idea

The workflow is built around two repository memory layers:

- `docs/` — durable product, architecture, and workflow context
- `specs/<feature-id>/` — per-feature intent, implementation plan, and task state

This keeps important context inside the repository instead of relying on hidden
chat/session memory.

## Main roles

- **User** — sets goals, approves direction, and makes final product decisions
- **Codex** — architect, reviewer, CI/CD owner, and orchestration layer
- **Claude Code** — primary implementation agent for product code
- **GitHub Actions** — runs required checks and AI review workflows
- **Human approver** — final merge authority

## Repository structure

- `.specify/` — process constitution and templates
- `docs/` — durable project memory
- `specs/` — feature execution artifacts
- `src/` — product code
- `tests/` — automated tests
- `scripts/` — orchestration and workflow utilities
- `skills/` — reusable agent guidance for specialized tasks
- `.github/` — CI/CD workflows and prompt templates

## Standard delivery loop

1. Start from current `main`
2. Read repository memory
3. Create or update `spec.md`, `plan.md`, and `tasks.md`
4. Create an isolated worktree for the implementation task
5. Launch the selected implementation agent
6. Implement code and tests
7. Open a PR
8. Run `baseline-checks`, `guard`, `python-checks`, and `AI Review`
9. Iterate on the same branch until the PR is merge-ready
10. Merge only when checks are green and blocking findings are gone

## Why this matters

This workflow makes development:

- reproducible
- reviewable
- easier to resume across sessions
- safer for multi-agent collaboration
- suitable as a demonstration of structured AI-assisted software delivery

## Recommended reading

- [Russian full process guide](C:\Users\User\FlatProject\flatscanner\README_PROCESS_RU.md)
- [Project docs](C:\Users\User\FlatProject\flatscanner\docs\README.md)
- [AI PR workflow](C:\Users\User\FlatProject\flatscanner\docs\ai-pr-workflow.md)
- [Claude worker orchestration](C:\Users\User\FlatProject\flatscanner\docs\claude-worker-orchestration.md)
- [Agent rules](C:\Users\User\FlatProject\flatscanner\AGENTS.md)
