# Implementation Plan: Switchable AI Reviewer

## Summary

Generalize the self-hosted PR review pipeline so one `AI Review` workflow can run either Codex CLI or Claude Code CLI, with the active reviewer chosen only from the repository variable `AI_REVIEW_AGENT` and `claude` as the fallback default.

## Files And Areas

- `AGENTS.md` and `CLAUDE.md` for updated review expectations
- `docs/adr/002-ai-development-workflow.md` for the durable review selection decision
- `docs/ai-pr-workflow.md` for the updated PR loop and required checks
- `docs/project/backend/backend-docs.md` and `docs/project/backend/self-hosted-runner.md` for runner and operations guidance
- `docs/claude-pr-playbook.md` and `docs/claude-worker-orchestration.md` for follow-up workflow alignment
- `.github/workflows/ai-review.yml` for the unified review job
- `.github/review/schemas/pr-review.schema.json` for the shared review result contract
- `.github/codex/prompts/pr-review.md` and `.github/claude/prompts/pr-review.md` for reviewer-specific prompts
- `scripts/run-ai-pr-review.ps1`, `scripts/run-codex-pr-review.ps1`, `scripts/run-claude-pr-review.ps1`, and `scripts/run-claude-pr-fix.ps1`
- `specs/004-switchable-ai-reviewer/` for execution tracking

## Proposed Workflow

1. `AI Review` starts on the self-hosted runner for a non-draft PR update
2. The workflow passes the repository variable `AI_REVIEW_AGENT` into a shared selector script
3. The selector script normalizes the value and falls back to `claude` if the variable is missing or invalid
4. The selector invokes the selected review adapter
5. The adapter builds PR context, runs the chosen local CLI, validates the shared result contract, updates the sticky AI review comment, and fails on `request_changes`
6. Claude fix runs continue to read the same sticky AI review comment on later fix iterations

## Risks

- Claude CLI review output must stay machine-readable enough to preserve blocking review behavior
- Review comment marker changes can break downstream automation if not updated consistently
- The runner-label migration must stay coordinated with live GitHub runner labels so workflow routing does not break during rollout

## Validation

- Confirm the PowerShell parser accepts the new and updated scripts
- Confirm the workflow YAML parses after the selector changes
- Confirm `run-ai-pr-review.ps1` resolves `claude`, `codex`, and invalid input as expected
- Confirm the sticky review comment marker is shared with `claude-fix`
- Confirm docs and agent instructions describe `AI_REVIEW_AGENT` as the only reviewer switch
