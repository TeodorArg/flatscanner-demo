# AI Pull Request Workflow

This document describes the operating loop between Claude Code, Codex review, GitHub Actions, and the human merge decision.

## Roles

- Claude Code writes product code and opens pull requests
- Codex owns architecture, review, and CI/CD policy
- GitHub Actions enforces automated checks
- A human remains the final merge authority

Codex may also launch Claude workers locally through CLI, but those workers still use the same pull-request and review path described below.

## Standard Delivery Loop

1. Select the active feature folder under `specs/<feature-id>/`
2. Either start Claude manually or have Codex launch a local Claude worker in an isolated worktree
3. Claude implements the scoped task in a feature branch
4. Claude updates `tasks.md` and any required `docs/` or spec files in the same PR
5. Claude opens a pull request using the repository template
6. GitHub Actions runs `baseline-checks`, `guard`, and `codex-review`
7. Codex posts or updates a sticky AI review comment in the pull request
8. If fixes are needed, trigger Claude on the same PR by either adding the `claude-fix` label or commenting `/claude-fix`
9. Claude reads the review findings, updates the same branch, and pushes follow-up commits
10. GitHub reruns the checks automatically on the updated branch
11. A human merges only after required checks are green and the PR is approved

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

Because GitHub does not automatically fan out new PR workflows from a workflow-authored push made with `GITHUB_TOKEN`, the `Claude Fix PR` workflow checks out the PR branch without persisted workflow credentials and relies on the machine-local git credentials on the self-hosted runner. That makes the follow-up push behave like a normal user-authenticated branch update so the standard PR checks rerun naturally.

## Local Claude Worker Launches

For new implementation work, Codex may launch Claude CLI locally with the repository orchestration scripts documented in `docs/claude-worker-orchestration.md`.

Guardrails:

- one task per worker
- one worktree per worker
- one PR per worker branch
- no more than three concurrent workers unless a future ADR changes the limit

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

## Lessons Learned

The first full live loop through worker launch, PR creation, review, automated fixes, and conflict resolution established these additional rules:

- A push authored by a GitHub workflow with `GITHUB_TOKEN` is not a reliable way to trigger the normal downstream PR checks
- The `Claude Fix PR` workflow should push with the self-hosted runner's local git credentials so the update behaves like a normal user-authenticated branch push
- A PR can look stale if the branch changed but a new check cascade never started; in that case, inspect the branch SHA before assuming Claude failed
- Sticky AI comments are authoritative summaries, but they can lag or describe the wrapper view of the run rather than every internal Claude action
- If an open PR and `main` both modify the same workflow files, resolve that conflict directly in the PR branch and rerun the normal checks on the merged result
- When the workflow definition itself changes on `main`, runs that were already started may still execute the older version of that workflow

## Current Practical Rule

Use automation for review and for follow-up fixes, but treat merge readiness as a combination of:

- the current PR head SHA
- the current required check results on that SHA
- the latest sticky Codex review comment
- human approval

That keeps the process resilient even when the automation layer itself is being improved in parallel with product work.
