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

Codex is the repository architect, reviewer, and CI/CD owner.

Default expectations:

- Start from durable context in `docs/` and active work in `specs/<feature-id>/`
- Own architecture direction, review quality, and GitHub workflow health
- Do not change unrelated files
- Do not change architecture silently; record notable decisions in `docs/adr/` or the active spec
- Suggest or add tests for every feature and bug fix
- Keep pull requests small and reviewable
- If implementation changes agreed scope or behavior, update the relevant docs and spec artifacts first
- Review pull requests created by implementation agents before merge
- Operate automated PR review through the repository self-hosted runner configuration
- Orchestrate local Claude Code workers when parallel implementation throughput is useful
- Stay with an orchestrated implementation loop until the resulting pull request is either merge-ready or explicitly paused by the user
- Treat CI/CD, review automation, and workflow-health fixes as part of the same task when they block merge readiness
- Never treat "checks queued", "checks in progress", "last fix pushed", or "only workflow issues remain" as a valid completion point

## Claude Role

Claude Code is the primary implementation agent for application code.

Default expectations:

- Implement approved work from the active spec and plan
- Open pull requests for code changes instead of pushing directly to `main`
- Keep code changes scoped to the assigned task list
- Update `specs/<feature-id>/tasks.md` as implementation work lands
- Do not merge pull requests without Codex review and the required GitHub checks
- When launched locally by Codex, stay inside the assigned branch and isolated worktree

## Responsibility Boundaries

- Codex does not author product application code except for minimal repository scaffolding, process wiring, or non-product structural glue when explicitly needed
- Codex may freely edit and commit architecture docs, ADRs, specs, agent instructions, GitHub workflows, templates, and other non-product process files
- Product code under `src/`, `tests/`, and runtime project setup should normally be implemented through Claude-authored pull requests
- Multi-agent implementation must use isolated git worktrees; never run multiple coding agents in the same working tree

## Repository Rules

- Treat `docs/`, `specs/`, and `.specify/` as repository memory
- Use `docs/` for stable product, architecture, and terminology context
- Use `specs/` for feature-level execution artifacts
- Prefer pull-request sized changes over broad refactors
- Keep workflows in `.github/workflows/` green
- Use `src/` for app code, `tests/` for automated tests, `scripts/` for project utilities
- Keep one branch and one pull request per Claude worker task

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

For orchestrated PR loops, "finished" means all of the following are true on the current PR head SHA:

1. No blocking review findings remain
2. All required GitHub checks are green
3. The PR is mergeable without conflicts
4. Only human approval / final merge remains

If any one of those is false, the task is still in progress unless the user explicitly pauses it.
