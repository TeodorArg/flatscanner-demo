# AGENTS.md

This repository uses a spec-driven workflow built on `github/spec-kit` and a small durable `docs/` layer for cross-feature context.

## Read Order

Before planning, reviewing, or proposing architecture changes, read files in this order:

1. `.specify/memory/constitution.md`
2. `docs/README.md`
3. `docs/project-idea.md`
4. `docs/project/frontend/frontend-docs.md`
5. `docs/project/backend/backend-docs.md`
6. `docs/adr/*.md`
7. `specs/*/spec.md`
8. `specs/*/plan.md`
9. `specs/*/tasks.md`
10. Only then inspect implementation files

## Codex Role

Codex is used here as a planner, reviewer, and test helper.

Default expectations:

- Start from durable context in `docs/` and active work in `specs/<feature-id>/`
- Do not change unrelated files
- Do not change architecture silently; record notable decisions in `docs/adr/` or the active spec
- Suggest or add tests for every feature and bug fix
- Keep pull requests small and reviewable
- If implementation changes agreed scope or behavior, update the relevant docs and spec artifacts first

## Repository Rules

- Treat `docs/`, `specs/`, and `.specify/` as repository memory
- Use `docs/` for stable product, architecture, and terminology context
- Use `specs/` for feature-level execution artifacts
- Prefer pull-request sized changes over broad refactors
- Keep workflows in `.github/workflows/` green
- Use `src/` for app code, `tests/` for automated tests, `scripts/` for project utilities

## Negative Rules

- Do not invent architecture that is not documented or requested
- Do not perform broad refactors while implementing a single feature
- Do not modify agent instructions unless the workflow itself is being updated
- Do not skip updating docs when a decision materially changes implementation

## Completion Rules

When a task is finished:

1. Update `specs/<feature-id>/tasks.md`
2. Mark completed items clearly
3. Record durable decisions in `docs/` or `docs/adr/` if they affect future work
4. Note any follow-up work in the same file or a new spec if scope changed
