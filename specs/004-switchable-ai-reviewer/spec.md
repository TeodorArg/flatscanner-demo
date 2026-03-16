# Feature Spec: Switchable AI Reviewer

## Context

The repository already has a self-hosted AI review workflow, but the active reviewer is hard-wired to Codex. The team now wants the same PR review pipeline to support either Codex CLI or Claude Code CLI, with the choice controlled only by one GitHub repository variable.

## Scope

- Make automated PR review selectable between Codex and Claude
- Keep one stable `AI Review` workflow and one stable required check
- Define one repository variable as the only control point for reviewer selection
- Preserve the existing sticky review comment and blocking verdict behavior
- Keep `claude-fix` compatible with the selected reviewer output

## Out Of Scope

- Per-PR reviewer overrides through labels or workflow inputs
- Replacing the self-hosted runner model
- Changing the human approval and merge rules
- Product application code changes

## Requirements

- Automated PR review must read the reviewer choice from the GitHub repository variable `AI_REVIEW_AGENT`
- Supported `AI_REVIEW_AGENT` values must be `claude` and `codex`
- If `AI_REVIEW_AGENT` is missing or invalid, the workflow must fall back to `claude`
- The repository must keep one required review check named `AI Review`
- Both review adapters must produce the same machine-readable review result contract
- The sticky AI review comment must stay single-instance per PR and must identify which reviewer produced it
- Claude fix follow-up runs must read the current sticky AI review comment regardless of whether Codex or Claude produced it
- Durable docs and agent instructions must describe the new review selection model

## Acceptance Criteria

- `.github/workflows/ai-review.yml` runs a single `AI Review` job that delegates to a shared selector script
- Repository scripts exist for Codex review, Claude review, and shared reviewer selection
- The GitHub runner docs explain how `AI_REVIEW_AGENT` controls review execution
- `claude-fix` continues to work against the new sticky AI review comment format
- Validation covers script parsing plus reviewer selection for `claude`, `codex`, and invalid values

## Open Questions

- Whether a future enhancement should allow a non-blocking shadow reviewer alongside the selected blocking reviewer
