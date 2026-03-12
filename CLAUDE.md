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

## Implementation Rules

- Respect the repository structure
- Write tests with each meaningful code change
- Avoid unrelated refactors
- Preserve architectural decisions recorded in docs and specs
- If implementation requires a scope change, update docs and spec artifacts first
- Keep files focused and reasonably small

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
