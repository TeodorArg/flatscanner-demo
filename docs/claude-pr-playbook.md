# Claude PR Response Playbook

This is a concrete Claude-facing checklist.

It does not define the repository-wide role model; the generic PR contract
lives in `docs/ai-pr-workflow.md`.

## Checklist

1. Read the active `spec.md`, `plan.md`, and `tasks.md`.
2. Implement only the scoped task on the assigned branch.
3. Update tests, specs, and docs when behavior or scope changes.
4. Open or update the same PR and include summary, tests run, and remaining
   risks.
5. Watch required checks and `AI Review`.
6. Treat the sticky `<!-- ai-review -->` comment as the current machine-review
   summary.
7. If findings remain, fix them on the same PR branch and rerun the loop.
8. Do not ask for merge until checks are green and only human approval remains.

## Fix Trigger

Maintainers can continue the same PR with `claude-fix` or `/claude-fix`.

## Suggested Prompt

`Review PR #<number>. Read the active feature spec, the PR diff, current check results, and the sticky AI review comment. Fix blocking findings in the same branch, update tests/docs/specs as needed, and push follow-up commits until only human approval remains.`
