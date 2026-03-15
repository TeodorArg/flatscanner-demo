# Tasks: AI Pull Request Workflow

## Spec

- [x] Define explicit Codex and Claude Code responsibilities
- [x] Record the pull-request based AI delivery model
- [x] Define the required automation and review gates

## Documentation

- [x] Update `AGENTS.md` with role boundaries and commit rules
- [x] Update `CLAUDE.md` with implementation and PR expectations
- [x] Add a durable ADR for the AI development workflow
- [x] Add a durable operations guide for the AI PR loop
- [x] Add a Claude-facing playbook for opening, monitoring, and fixing PRs

## GitHub Workflow

- [x] Replace the placeholder AI review workflow with a self-hosted Codex PR review workflow
- [x] Add a durable Codex review prompt file
- [x] Add a structured review schema for machine-readable results
- [x] Add a pull request template for AI-authored work
- [x] Add default repository ownership metadata
- [x] Add local runner setup and review orchestration scripts
- [x] Replace the temporary local adapter concept with direct local `codex exec` review execution
- [x] Add a self-hosted Claude PR fix workflow triggered by label or PR comment

## Validation

- [x] Register the Windows self-hosted runner with the `codex` label
- [x] Ensure the runner uses the same authenticated Windows user profile as local Codex CLI
- [x] Enable branch protection rules for `main`
- [x] Confirm required checks include `CI`, `PR Guard`, and `AI Review`
- [x] Confirm at least one human approval is required before merge
- [x] Open a test pull request and verify sticky review comments plus blocking verdict behavior
- [x] Open a test pull request and verify the `Claude Fix PR` workflow can update the same PR branch
- [x] Eliminate false `codex-review` exit `1` failures on approve paths and print durable diagnostics in the GitHub run logs

## Follow-Up

- [ ] Decide whether Claude PR creation should later be triggered from issues or slash commands
- [ ] Decide whether low-severity review findings should remain non-blocking forever
