# Project Constitution

## Purpose

`flatscanner` is developed with a spec-driven, AI-assisted workflow.

## Core Principles

1. Specs before code.
2. Pull requests are the unit of review and merge.
3. CI checks must pass before merge.
4. Agents must preserve project context through repository files, not hidden session state.
5. Durable context and feature execution artifacts should be separated.

## Source Of Truth

Repository truth is split across two layers:

- `docs/`: durable product, architecture, glossary, and ADR context shared across features
- `specs/<feature-id>/`: active feature intent, plan, validation, and execution checklist

The process contract and templates live in `.specify/`.

Each feature folder should contain:

- `spec.md`: product intent, scope, requirements, acceptance criteria
- `plan.md`: technical approach, touched areas, risks, validation
- `tasks.md`: execution checklist

## Agent Roles

- ChatGPT: product framing, architecture discussion, tradeoff analysis
- Codex: planning, review, test guidance, PR analysis
- Claude Code: implementation, multi-file changes, refactors aligned with spec

## Quality Gates

No change should be merged unless:

- the relevant docs and spec are up to date
- tests are present when behavior changes
- GitHub Actions checks pass
- pull request review is completed
