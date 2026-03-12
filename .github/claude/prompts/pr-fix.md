Claude Code is acting as the implementation agent for an existing pull request.

Before making changes:

1. Read `AGENTS.md`
2. Read `CLAUDE.md`
3. Read `docs/README.md`
4. Read `docs/project-idea.md`
5. Read `docs/project/backend/backend-docs.md`
6. Read `docs/ai-pr-workflow.md`
7. Read `docs/claude-pr-playbook.md`
8. Read the active feature folder under `specs/<feature-id>/`

Task:

- Work only on the current pull request branch
- Read the current pull request diff, the sticky Codex review comment, and any human review comments
- Fix the blocking findings in the same branch
- Update tests, docs, and spec artifacts when needed
- Keep the change scoped to the review findings and the active feature intent
- Do not merge or open a new pull request

Output rules:

- After making changes, return JSON matching the provided schema
- Summarize what was changed, what tests were run, and any follow-up needed
