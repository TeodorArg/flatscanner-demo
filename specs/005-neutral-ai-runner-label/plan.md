# Implementation Plan: Neutral AI Runner Label

## Summary

Rename the self-hosted GitHub Actions runner label used by repository automation from `codex` to `ai-runner`, then update repository workflows, setup scripts, and durable docs so the runner infrastructure matches the switchable AI reviewer design.

## Files And Areas

- `.github/workflows/ai-review.yml` and `.github/workflows/claude-fix-pr.yml` for the new `runs-on` label
- `scripts/setup-self-hosted-runner.ps1` for the default runner labels
- `scripts/` for a migration helper that adds `ai-runner` to an existing runner
- `docs/project/backend/backend-docs.md` and `docs/project/backend/self-hosted-runner.md` for operator guidance
- `docs/ai-pr-workflow.md`, `docs/adr/002-ai-development-workflow.md`, and `docs/adr/003-local-claude-worker-orchestration.md` for durable workflow alignment
- `specs/004-switchable-ai-reviewer/tasks.md` and `specs/005-neutral-ai-runner-label/` for execution tracking

## Proposed Workflow

1. Add the neutral `ai-runner` label to the existing self-hosted GitHub runner
2. Update repository workflows to target `ai-runner`
3. Update runner setup defaults so newly registered runners use `ai-runner`
4. Document the migration and add a helper script so operators can reapply labels consistently
5. Validate that GitHub sees the runner with `ai-runner` and that repository workflow files parse cleanly

## Risks

- If workflows are switched before the live runner has the new label, review automation will queue indefinitely
- If the old `codex` label is removed too early, any stale workflow run or manual command that still expects it may stop scheduling
- Docs and automation can drift again if the migration helper is not kept repository-local and visible

## Validation

- Confirm the PowerShell parser accepts the new or updated scripts
- Confirm workflow YAML parses after the `runs-on` label change
- Confirm GitHub reports the existing runner with the `ai-runner` label
- Confirm durable docs and ADRs consistently describe `ai-runner` as the required runner label
