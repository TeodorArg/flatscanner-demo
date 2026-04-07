# Tasks: Checkpoint Decision Helper

## Status

- [x] Feature folder created
- [x] Canonical `spec.md` created
- [x] Canonical `plan.md` created
- [x] Canonical `tasks.md` created

## Phase 1. Freeze Helper Contract

- [x] Define the canonical decision enum
- [x] Define the helper input modes
- [x] Define the reasoning output shape
- [x] Freeze the representative scenario matrix

## Phase 2. Open Implementation Loop

- [x] Open an isolated implementation worktree/branch/PR for `051`
- [x] Implement the read-only helper command
- [x] Keep the helper write-free in v1

## Phase 3. Validation

- [x] Add automated tests for the scenario matrix
- [x] Validate `neither`
- [x] Validate `lightrag_only`
- [x] Validate `mcp_local_only`
- [x] Validate `both`
- [x] Run `python scripts/checkpoint_decision.py decide --git-diff`
- [x] Record the current branch checkpoint outcome before commit/PR finalization
- [x] Explicitly defer checkpoint apply work to `052-checkpoint-apply-pipeline`
- [x] Confirm that `LightRAG`/MCP/local-memory apply actions remain out of scope for this read-only helper feature

## Completion Criteria

- [x] The helper returns one stable decision per scenario
- [x] The helper explains why the decision was chosen
- [x] The helper performs no rebuild or sync writes in v1
- [ ] The implementation lands only through the standard isolated worktree/PR loop

## Execution Note

- [x] Product-code and runtime changes for this helper must not be implemented in the main checkout

Current branch checkpoint outcome before commit/PR finalization:

- `both`

For this feature, the outcome is recorded but not applied. Downstream
`LightRAG`, MCP memory, and local mirror apply work is intentionally deferred
to `052-checkpoint-apply-pipeline`.
