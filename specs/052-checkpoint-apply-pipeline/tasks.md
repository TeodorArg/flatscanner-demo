# Tasks: Checkpoint Apply Pipeline

## Status

- [x] Feature folder created
- [x] Canonical `spec.md` created
- [x] Canonical `plan.md` created
- [x] Canonical `tasks.md` created

## Phase 1. Freeze Apply Contract

- [x] Define the post-`051` apply flow
- [x] Define the outcome-to-action mapping
- [x] Define the canonical apply order for `LightRAG`, MCP, and local mirror
- [x] Define the reporting contract for applied versus skipped steps

## Phase 2. Open Implementation Loop

- [ ] Open an isolated implementation worktree/branch/PR for `052`
- [ ] Implement the repository-local apply command
- [ ] Reuse the `051` decision helper instead of duplicating policy logic

## Phase 3. Validation

- [ ] Add automated tests for `neither`, `lightrag_only`, `mcp_local_only`, and `both`
- [ ] Validate that `neither` skips all apply steps
- [ ] Validate that `lightrag_only` runs only the `LightRAG` path
- [ ] Validate that `mcp_local_only` runs MCP/local follow-up in the correct order
- [ ] Validate that `both` runs the full apply path in the correct order

## Completion Criteria

- [ ] The repository has one standard checkpoint apply flow after `051`
- [ ] The apply layer runs only the steps required by the decision outcome
- [ ] Canonical file ordering remains intact
- [ ] The implementation lands only through the standard isolated worktree/PR loop

## Execution Note

This feature is the apply-layer follow-up to `051`; it must not be implemented
in the main checkout.
