# Claude PR Response Playbook

Use this playbook when Claude Code is asked to create, update, or finish a pull request.

## Opening A PR

1. Start from the active feature folder in `specs/<feature-id>/`
2. Implement only the scoped task in a feature branch
3. Update `spec.md`, `plan.md`, `tasks.md`, and relevant `docs/` files if the change affects behavior, scope, architecture, or validation state
4. Run the relevant tests
5. Open a pull request using the repository template
6. In the PR body, include:
   - active feature folder
   - summary of changes
   - tests run
   - remaining risks or follow-up work

## Monitoring The PR

After opening or updating the PR, check:

- required checks: `baseline-checks`, `guard`, `codex-review`
- the sticky Codex review comment marked with `<!-- codex-ai-review -->`
- any human review comments in the PR thread

## Handling Codex Review Findings

If `codex-review` reports findings or fails:

1. Read the current sticky Codex review comment fully
2. Treat the listed findings as the authoritative machine-review issues for this PR iteration
3. Fix the findings in the same PR branch
4. Add or update tests, docs, and spec artifacts when called out by the review
5. Push follow-up commits to the same branch
6. Wait for a fresh run of `baseline-checks`, `guard`, and `codex-review`
7. Re-read the updated sticky review comment
8. Repeat until the PR is green and no blocking findings remain

## Semi-Automatic Fix Trigger

A maintainer can ask Claude to continue work on an existing PR by either:

- adding the label `claude-fix`
- adding a PR comment containing `/claude-fix`

That triggers the `Claude Fix PR` workflow on the self-hosted runner. Claude then reads the PR context, the sticky Codex review comment, and the active spec before pushing follow-up commits to the same branch.

## Rules While Iterating

- Do not open a replacement PR for the same work unless explicitly instructed
- Do not ask for merge while `codex-review` is red
- Do not ignore missing spec or docs updates when they are part of the review findings
- Keep the PR scoped; if the work grows, update the spec first instead of silently expanding the implementation

## Ready For Merge

A PR is ready for merge only when:

- `baseline-checks` is green
- `guard` is green
- `codex-review` is green
- the PR has at least one human approval
- the active spec artifacts are up to date

## Suggested Prompt To Claude

Use this when handing Claude an existing PR to finish:

`Review PR #<number>. Read the active feature spec, the current PR diff, all required check results, and the sticky Codex review comment. Fix the blocking findings in the same branch, update tests/docs/specs as needed, and push follow-up commits until the PR is ready for human approval.`
