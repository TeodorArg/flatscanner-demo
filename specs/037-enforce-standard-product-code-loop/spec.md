# Feature Spec: Enforce Standard Product-Code Loop

## Goal

Reduce process drift by making the standard product-code loop harder to bypass
both in repository instructions and in CI guardrails.

## Problem

The current repository memory strongly prefers the Claude worker + PR loop for
product code, but the wording is still soft in places and the PR guard only
checks for *some* docs or spec changes alongside code changes.

That leaves room for accidental local implementation in `src/`, `tests/`, or
runtime setup without the full feature-memory loop.

## Scope

In scope:

- strengthen `AGENTS.md` from preference to hard-stop rules
- document the hard gate in the shared AI PR workflow
- make `PR Guard` require a complete active feature folder when product code
  changes land in a PR

Out of scope:

- changing implementation-agent selection itself
- changing review-agent selection itself
- adding local pre-commit hooks

## Acceptance Criteria

- `AGENTS.md` explicitly forbids direct Codex edits to product code
- `docs/ai-pr-workflow.md` records the hard-stop rule for blocked worker loops
- `PR Guard` fails when product code changes do not include a complete
  `specs/<feature-id>/spec.md`, `plan.md`, and `tasks.md` update
