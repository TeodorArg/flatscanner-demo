# repo-memory-platform: process overview

## What This Repository Is

This repository is a reusable platform for spec-driven, AI-assisted software
delivery with explicit repository memory.

It is being migrated away from the legacy `flatscanner` demo into a
vendor-neutral model where:

- files remain canonical
- `docs/` and `specs/` carry project memory
- work moves through isolated branches, pull requests, checks, and review
- retrieval tooling is optional and derivative

## Memory Layers

- `docs/` for durable product, architecture, and process context
- `specs/<feature-id>/` for feature intent, plan, and execution state
- `.specify/` for constitution and process templates

This keeps important context in the repository rather than in hidden session
memory.

## Main Roles

- **Human requester** sets goals and approves product direction
- **Orchestrator** reads repository memory, shapes specs, and drives the loop
- **Implementation agent** makes scoped changes in an isolated worktree
- **Review agent** inspects PRs and raises findings
- **GitHub Actions / checks** run required validation
- **Human approver** remains the final merge authority

Concrete vendors for implementation and review agents may vary by repository
configuration. The role model stays the same.

## Repository Structure

- `.specify/` for process constitution and templates
- `docs/` for durable repository memory
- `specs/` for feature execution artifacts
- `src/` for implementation code
- `tests/` for automated validation
- `scripts/` for orchestration and workflow utilities
- `.github/` for CI/CD workflows and AI review assets

## Standard Delivery Loop

1. Start from current `main`
2. Read repository memory
3. Create or update `spec.md`, `plan.md`, and `tasks.md`
4. Create an isolated branch and worktree for product-code work
5. Run the selected implementation agent
6. Update code, tests, and task state
7. Open or update the PR
8. Run required checks and AI review
9. Iterate on the same branch until the PR is merge-ready
10. Merge only when checks are green and blocking findings are cleared

## Retrieval Principle

Repository files remain the source of truth.

If retrieval tooling such as `LightRAG` is added, it must:

- index repository knowledge without replacing canonical files
- respect mandatory process documents
- reduce context load without hiding governing rules

The canonical policy for mandatory context, retrieved context, and the pilot
corpus lives in `docs/context-policy.md`.

The canonical workflow for context budgets, bootstrap order, retrieval
triggers, and the `LightRAG` versus MCP/local-memory checkpoint checklist lives
in `docs/context-economy-workflow.md`.

## Recommended Reading

- [Russian process guide](./README_PROCESS_RU.md)
- [Repository docs layer](./docs/README.md)
- [Project idea](./docs/project-idea.md)
- [Repository rules](./AGENTS.md)
- [AI PR workflow](./docs/ai-pr-workflow.md)
