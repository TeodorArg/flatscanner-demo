# AI Pull Request Workflow

This is the canonical PR-loop document for implementation, review, and merge
readiness.

## Roles

- The selected implementation agent writes product code and updates the active
  feature folder.
- The orchestrator owns architecture, review policy, and CI/CD health.
- GitHub Actions runs required checks.
- The selected review agent produces machine-review findings.
- A human remains the final merge authority.

Concrete automation may still use vendor-specific script names, labels, or
workflow entries. Those implementation details do not redefine the generic role
model.

## Standard Loop

1. Start from current `main`.
2. Work from an active `specs/<feature-id>/` folder.
3. The implementation agent works on a feature branch, either manually or
   through local worker orchestration.
4. After canonical doc/spec/task updates, run
   `python scripts/checkpoint_decision.py decide --git-diff` before finalizing
   commit or PR state.
5. Apply the checkpoint outcome:
   - run `LightRAG` refresh/rebuild validation when the outcome is
     `lightrag_only` or `both`
   - update MCP memory when the outcome is `mcp_local_only` or `both`
   - refresh local `in_memory/memory.jsonl` only when local parity is useful
6. The PR updates `tasks.md`, tests, and any required durable docs.
7. GitHub runs required checks and `AI Review`.
8. The selected reviewer posts or updates one sticky comment marked
   `<!-- ai-review -->`.
9. If follow-up is needed, continue on the same branch.
10. A human merges only after required checks are green and approval is present.

## Hard Gate

- The orchestrator must not bypass this loop for product code in `src/`,
  `tests/`, or runtime setup.
- Product-code work starts only after the active feature folder exists and the
  isolated branch/worktree is created.
- If the implementation worker, isolated worktree flow, or PR loop is
  unavailable, stop and report the blocker instead of implementing locally.
- Local unreviewed product-code edits do not count as progress toward
  completion.

## AI Review Contract

- Reviewer selection comes only from the repo variable `AI_REVIEW_AGENT`.
- The required status check is always `AI Review`.
- Self-hosted review workflows target the neutral runner label `ai-runner`.

Concrete supported reviewer values and fallback rules are implementation details
of the active workflow configuration and should be kept synchronized with
`.github/workflows/`.

## Merge-Ready Rule

The loop is still active while any of these are true:

- required checks are queued, running, or red
- blocking findings remain on the current head SHA
- the PR has merge conflicts
- only workflow or runner issues remain unresolved

A task is done only when the current PR head SHA has green required checks, no
blocking findings, no conflicts, and only human approval or final merge
remaining.

## Related Docs

- Local worker example: `docs/claude-worker-orchestration.md`
- Concrete Claude PR checklist: `docs/claude-pr-playbook.md`
