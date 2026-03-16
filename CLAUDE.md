# CLAUDE.md

Claude Code is the primary implementation agent for product code in this repo.

## Read Before Coding

1. `.specify/memory/constitution.md`
2. `docs/README.md`
3. durable docs relevant to the task
4. the active `specs/<feature-id>/spec.md`, `plan.md`, and `tasks.md`
5. only then the relevant code

## Contract

- Work from an approved active feature folder.
- Stay within the assigned branch and isolated worktree when Codex launches you locally.
- Keep changes scoped; avoid unrelated cleanup.
- Add or update tests with meaningful behavior changes.
- Update `tasks.md`, and update `docs/` or `specs/` in the same PR when scope, behavior, or architecture changes.
- Open or update a PR instead of merging directly to `main`.

## PR Loop

- Use the repository PR template and name the active feature folder.
- Wait for `baseline-checks`, `guard`, and `AI Review`.
- Treat the sticky `<!-- ai-review -->` comment as the current machine-review summary.
- If `AI Review` or `/claude-fix` asks for follow-up, keep working on the same PR branch until checks are green and blocking findings are resolved.
- Do not merge manually; merge happens only after required checks and human approval.

## Negative Rules

- Do not introduce architecture silently.
- Do not add dependencies or behavior changes without documentation.
- Do not assume another Claude worker owns the same files; if scope overlaps, stay inside the assigned task.
