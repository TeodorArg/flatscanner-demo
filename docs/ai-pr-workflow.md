# AI Pull Request Workflow

This document describes the operating loop between Claude Code, Codex review, GitHub Actions, and the human merge decision.

## Roles

- Claude Code writes product code and opens pull requests
- Codex owns architecture, review, and CI/CD policy
- GitHub Actions enforces automated checks
- A human remains the final merge authority

## Standard Delivery Loop

1. Select the active feature folder under `specs/<feature-id>/`
2. Claude implements the scoped task in a feature branch
3. Claude updates `tasks.md` and any required `docs/` or spec files in the same PR
4. Claude opens a pull request using the repository template
5. GitHub Actions runs `baseline-checks`, `guard`, and `codex-review`
6. Codex posts or updates a sticky AI review comment in the pull request
7. If fixes are needed, trigger Claude on the same PR by either adding the `claude-fix` label or commenting `/claude-fix`
8. Claude reads the review findings, updates the same branch, and pushes follow-up commits
9. GitHub reruns the checks automatically on the updated branch
10. A human merges only after required checks are green and the PR is approved

## How Claude Should Handle Review Feedback

- Treat the Codex review comment as the authoritative machine-review summary for the PR iteration
- Read both the verdict and the individual findings
- Update the same PR branch rather than opening a replacement PR
- Resolve the code issue and also resolve missing docs, tests, or spec updates when called out
- Push the follow-up commits and wait for a fresh `codex-review` run
- Repeat until the review is clear enough for human approval

## Automated Claude Fix Trigger

You can trigger Claude to work on an existing PR in two ways:

- add the label `claude-fix` to the pull request
- add an issue comment containing `/claude-fix`

That starts the `Claude Fix PR` workflow on the self-hosted runner running on this computer.

## How Codex Review Appears

- The self-hosted runner executes local `codex exec` on every non-draft PR update
- The workflow posts a sticky comment marked with `<!-- codex-ai-review -->`
- The same comment is updated on subsequent pushes, so the PR keeps one current review summary instead of accumulating many stale comments
- If the review verdict is `request_changes`, the `codex-review` check fails and blocks merge

## Current Required Checks

- `baseline-checks`
- `guard`
- `codex-review`

## Merge Rule

Do not merge to `main` unless all required checks are green and at least one human approval is present.
