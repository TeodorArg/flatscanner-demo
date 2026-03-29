# Technical Plan: Enforce Standard Product-Code Loop

## Approach

Add one human-facing guardrail and one machine-enforced guardrail.

## Planned Changes

1. Tighten `AGENTS.md` language:
   - direct Codex edits to product code are not allowed
   - if the Claude worker or PR loop is unavailable, stop and report the blocker
   - local draft product-code work does not count as progress
2. Update `docs/ai-pr-workflow.md` with a dedicated hard-gate section
3. Extend `.github/workflows/pr-guard.yml` so product-code PRs must touch a
   complete `spec.md + plan.md + tasks.md` set within one feature folder

## Validation

- review the changed instructions for consistency
- inspect the workflow logic against the expected file patterns
- verify the new feature-memory requirement is explicit in the guard output
