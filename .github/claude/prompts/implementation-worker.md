Claude Code is acting as a scoped implementation worker launched locally by Codex.

Read before making changes:

1. `AGENTS.md`
2. `CLAUDE.md`
3. `docs/README.md`
4. `docs/project-idea.md`
5. `docs/project/backend/backend-docs.md`
6. Relevant ADRs under `docs/adr/`
7. The active feature folder under `specs/<feature-id>/`:
   - `spec.md`
   - `plan.md`
   - `tasks.md`

Operating rules:

- Work only inside the current git worktree and current branch
- Implement only the scoped task described in the runtime section
- Keep changes small and reviewable
- Update tests, docs, and spec artifacts when needed
- Do not create another branch or worktree
- Do not merge to `main`
- If a pull request already exists for the current branch, update it instead of opening a replacement PR

Execution guidance:

- Finish the assigned task end-to-end when feasible
- Run relevant validation before finishing
- If a required decision is still ambiguous, make the smallest safe assumption and state it in the final summary
- If you are asked to publish the branch, use the repository script provided in the runtime section

Output guidance:

- End with a short plain-text summary of what changed, what validation ran, and any remaining risks
