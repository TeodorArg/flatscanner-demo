# AI Pull Request Workflow

This is the canonical PR-loop document for implementation, AI review, and merge readiness.

## Roles

- Claude writes product code and updates the active feature folder.
- Codex owns architecture, review policy, and CI/CD health.
- GitHub Actions runs required checks.
- A human remains the final merge authority.

## Standard Loop

1. Start from current `main`.
2. Work from an active `specs/<feature-id>/` folder.
3. Claude implements on a feature branch, either manually or through the local worker orchestration flow.
4. The PR updates `tasks.md`, tests, and any required durable docs.
5. GitHub runs `baseline-checks`, `guard`, and `AI Review`.
6. The selected reviewer posts or updates one sticky comment marked `<!-- ai-review -->`.
7. If follow-up is needed, continue on the same branch. Maintainers may trigger `Claude Fix PR` with the `claude-fix` label or `/claude-fix`.
8. A human merges only after required checks are green and approval is present.

## AI Review Contract

- Reviewer selection comes only from the repo variable `AI_REVIEW_AGENT`.
- Supported values are `claude` and `codex`; missing or invalid values fall back to `claude`.
- The required status check is always `AI Review`.
- Low-severity-only findings are advisory; the effective verdict is normalized to `comment`.
- `AI Review` fails only when the effective verdict remains `request_changes`.
- Self-hosted review workflows target the neutral runner label `ai-runner`.

## Claude Fix Contract

- `Claude Fix PR` works on the existing PR branch rather than opening a replacement PR.
- The workflow uses the runner's local git credentials so normal downstream PR checks rerun after follow-up pushes.
- Each fix run writes a fresh PR comment; AI review stays a sticky single-comment summary.

## Merge-Ready Rule

The loop is still active while any of these are true:

- required checks are queued, running, or red
- blocking findings remain on the current head SHA
- the PR has merge conflicts
- only workflow or runner issues remain unresolved

A task is done only when the current PR head SHA has green required checks, no blocking findings, no conflicts, and only human approval or final merge remaining.

## Related Docs

- Runner setup and diagnostics: `docs/project/backend/self-hosted-runner.md`
- Local worker launches: `docs/claude-worker-orchestration.md`
- Claude-facing PR checklist: `docs/claude-pr-playbook.md`
