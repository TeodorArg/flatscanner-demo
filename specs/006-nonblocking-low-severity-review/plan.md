# Implementation Plan: Non-Blocking Low-Severity AI Review Findings

## Summary

Make the required `AI Review` check deterministic by normalizing reviewer output so low-severity-only findings remain advisory. This keeps medium and high findings eligible to block merge while preventing low-severity noise from failing the workflow.

## Files And Areas

- `.github/codex/prompts/pr-review.md` and `.github/claude/prompts/pr-review.md` for reviewer instructions
- `scripts/` for shared AI review verdict normalization and local validation
- `scripts/run-codex-pr-review.ps1` and `scripts/run-claude-pr-review.ps1` for effective verdict handling
- `docs/ai-pr-workflow.md` and `docs/adr/002-ai-development-workflow.md` for durable policy documentation
- `specs/002-ai-pr-workflow/tasks.md` and `specs/006-nonblocking-low-severity-review/` for execution tracking

## Proposed Workflow

1. The selected AI reviewer returns its JSON review result as today
2. A shared normalization layer inspects the returned verdict and finding severities
3. If the reviewer requested changes but all findings are `low` or no findings exist, the effective verdict is downgraded to `comment`
4. The sticky AI review comment shows the normalized verdict and any policy note
5. The workflow fails only when the effective verdict remains `request_changes`

## Risks

- Policy normalization can become opaque if the sticky comment does not explain when a downgrade happened
- Codex and Claude adapters can drift if the normalization logic is duplicated or partially updated
- Review prompts can keep producing blocking low-severity verdicts if the written policy is not updated alongside the script behavior

## Validation

- Parse the updated PowerShell scripts successfully
- Run a local validation script that covers low-only, medium/high, and no-finding verdict combinations
- Confirm durable docs and prompts describe low-severity findings as advisory
