# CLAUDE.md

This repository uses a spec-first workflow with stable project docs and feature specs.

## Read Before Coding

Read these files before implementation:

1. `.specify/memory/constitution.md`
2. `docs/README.md`
3. `docs/project-idea.md`
4. `docs/project/frontend/frontend-docs.md`
5. `docs/project/backend/backend-docs.md`
6. The active feature folder in `specs/<feature-id>/`:
   - `spec.md`
   - `plan.md`
   - `tasks.md`

Then inspect only the relevant code.

## Role

Claude Code is the primary implementation agent for this repository.

## Implementation Rules

- Respect the repository structure
- Write tests with each meaningful code change
- Avoid unrelated refactors
- Preserve architectural decisions recorded in docs and specs
- If implementation requires a scope change, update docs and spec artifacts first
- Keep files focused and reasonably small
- Open pull requests for code changes instead of merging directly to `main`
- Expect Codex review plus required GitHub checks before merge

## PR Contract

- Work only from an approved active feature folder under `specs/<feature-id>/`
- Create a feature branch for every product code task
- If Codex launches you in an isolated worktree, treat that worktree and branch as your only allowed workspace
- Never push product code directly to `main`
- Update `specs/<feature-id>/tasks.md` before or with the PR when task state changes
- If behavior, scope, or architecture changes, update the relevant `docs/` and `specs/` files in the same PR
- Use the repository pull request template and identify the active feature folder explicitly
- In every PR, document what changed, what tests were run, and any remaining risks or follow-up work
- Wait for `baseline-checks`, `guard`, and `codex-review` to finish before asking for merge
- If `codex-review` reports findings, update the same PR branch and push follow-up commits until checks pass and review concerns are resolved
- If a maintainer triggers `claude-fix` or comments `/claude-fix`, continue working on that same PR branch instead of creating a new PR
- Do not merge pull requests manually; merge happens only after the required checks and human approval

## Negative Rules

- Do not introduce new architecture silently
- Do not change unrelated files to "clean things up"
- Do not add dependencies without documenting why
- Do not leave behavior changes undocumented

## Working Style

- Prefer small, focused changes
- Keep naming and file placement consistent
- Leave concise comments only where intent is not obvious
- Use pull requests as the unit of review
- Treat `specs/<feature-id>/tasks.md` as the execution checklist and keep it current
- Never assume another Claude worker is editing the same files; if the prompt scope suggests overlap, stop and stay within the assigned task
