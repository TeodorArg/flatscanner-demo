# Project Constitution

## Purpose

This repository uses a spec-driven, AI-assisted workflow with explicit
repository memory.

## Core Principles

1. Specs before code.
2. Pull requests are the unit of review and merge.
3. Required checks must pass before merge.
4. Repository files preserve context; hidden session state does not define
   project truth.
5. Durable memory, feature memory, and process memory must stay distinct.
6. Retrieval may assist context assembly, but canonical truth remains in files.

## Source Of Truth

Repository truth is split across these layers:

- `docs/` for durable product, architecture, and workflow context
- `specs/<feature-id>/` for feature intent, plan, and execution state
- `.specify/` for governing process rules and templates

Historical artifacts may exist, but they must be clearly separated from active
canonical memory.

Each feature folder should contain:

- `spec.md`: product intent, scope, requirements, acceptance criteria
- `plan.md`: technical approach, touched areas, risks, validation
- `tasks.md`: execution checklist and state

## Role Model

- Human requester: sets goals and approves direction
- Orchestrator: reads memory, frames scope, and drives the delivery loop
- Implementation agent: makes scoped changes in isolated work
- Review agent: evaluates pull requests and raises findings
- CI/checks: provide required machine validation
- Human approver: decides final merge

Concrete tools or vendors may implement these roles, but the repository
constitution does not bind them to one provider.

## Quality Gates

No change should be treated as complete unless:

- the relevant docs and spec are up to date
- tests are present when behavior changes
- required checks pass
- pull request review is completed
