# Feature Spec: Neutral AI Runner Label

## Context

The repository now supports switchable AI review between Claude and Codex, but the self-hosted GitHub runner is still labeled `codex`. That historical label no longer reflects the runner's role and creates unnecessary architecture drift between live infrastructure and the repository docs.

## Scope

- Rename the repository's self-hosted runner label from `codex` to an agent-neutral label
- Update GitHub workflows to target the neutral label
- Update runner setup and migration scripts for the new label
- Update durable docs and ADRs so the runner model matches the current workflow design
- Add a repository-local helper for applying the runner-label migration in GitHub

## Out Of Scope

- Changing the reviewer-selection model
- Replacing the self-hosted runner architecture
- Product application code changes
- Renaming `codex/` branch prefixes or Codex-specific role descriptions

## Requirements

- The self-hosted runner label used by repository workflows must be `ai-runner`
- `.github/workflows/ai-review.yml` and `.github/workflows/claude-fix-pr.yml` must target `ai-runner`
- Runner setup instructions and setup scripts must default to `ai-runner`
- The repository must provide a repeatable helper script for adding `ai-runner` to an existing runner
- Durable docs and ADRs must explain the label migration and the neutral runner intent
- Validation must confirm workflow YAML parsing, PowerShell parser success, and live runner-label visibility in GitHub

## Acceptance Criteria

- All repository workflows that depend on the self-hosted review runner use `ai-runner`
- `scripts/setup-self-hosted-runner.ps1` defaults to `ai-runner`
- A repository-local script exists for adding the `ai-runner` label to an existing GitHub runner
- Durable docs no longer describe `codex` as the required runner label for AI review
- GitHub shows the current runner with the `ai-runner` label before the branch is considered ready

## Resolution

- The migration helper keeps the legacy `codex` runner label by default and only removes it through an explicit operator opt-in
