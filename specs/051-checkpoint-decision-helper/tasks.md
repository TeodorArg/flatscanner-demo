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

- [ ] Open an isolated implementation worktree/branch/PR for `051`
- [ ] Implement the read-only helper command
- [ ] Keep the helper write-free in v1

## Phase 3. Validation

- [ ] Add automated tests for the scenario matrix
- [ ] Validate `neither`
- [ ] Validate `lightrag_only`
- [ ] Validate `mcp_local_only`
- [ ] Validate `both`

## Completion Criteria

- [ ] The helper returns one stable decision per scenario
- [ ] The helper explains why the decision was chosen
- [ ] The helper performs no rebuild or sync writes in v1
- [ ] The implementation lands only through the standard isolated worktree/PR loop

## Execution Note

- [ ] Product-code and runtime changes for this helper must not be implemented in the main checkout
