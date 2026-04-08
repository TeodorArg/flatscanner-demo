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
- [x] Implement the repository-local apply command
- [x] Reuse the `051` decision helper instead of duplicating policy logic

## Phase 3. Validation

- [x] Add automated tests for `neither`, `lightrag_only`, `mcp_local_only`, and `both`
- [x] Validate that `neither` skips all apply steps
- [x] Validate that `lightrag_only` runs only the `LightRAG` path
- [x] Validate that `mcp_local_only` runs MCP/local follow-up in the correct order
- [x] Validate that `both` runs the full apply path in the correct order

## Completion Criteria

- [x] The repository has one standard checkpoint apply flow after `051`
- [x] The apply layer runs only the steps required by the decision outcome
- [x] Canonical file ordering remains intact
- [ ] The implementation lands only through the standard isolated worktree/PR loop

## Execution Note

This feature is the apply-layer follow-up to `051`; it must not be implemented
in the main checkout.

Current implementation-loop status in the isolated worktree:

- branch/worktree: `feat/052-checkpoint-apply-pipeline` at `/tmp/flatscanner-demo-052-apply`
- implemented entrypoint: `scripts/checkpoint_apply.py`
- implemented shared module: `src/repo_memory/checkpoint_apply.py`
- added scenario tests: `tests/test_checkpoint_apply.py`
- non-clean `LightRAG` build path in `src/repo_memory/lightrag_pilot.py` now uses selective delete+reinsert refresh planning for changed, added, removed, and duplicate-artifact files instead of re-inserting the whole corpus
- canonical workflow docs updated to reference the apply entrypoint

Current validation status in this environment:

- `uv sync --extra dev --extra repo_memory` succeeded in the isolated worktree environment
- `uv run python -m pytest tests/test_checkpoint_decision.py tests/test_checkpoint_apply.py -q` passed (`13 passed`)
- `.venv/bin/python -m pytest tests/test_lightrag_pilot.py -q` passed after adding duplicate-aware rebuild regression coverage (`34 passed`)
- `.venv/bin/python -m pytest tests/test_checkpoint_decision.py tests/test_checkpoint_apply.py tests/test_lightrag_pilot.py -q` passed (`47 passed`)
- `uv run python -m py_compile src/repo_memory/checkpoint_apply.py scripts/checkpoint_apply.py tests/test_checkpoint_apply.py` passed
- `.venv/bin/python -m py_compile src/repo_memory/lightrag_pilot.py tests/test_lightrag_pilot.py` passed
- `uv run python scripts/checkpoint_apply.py apply --path notes/draft.txt --format text` passed and confirmed the `neither` skip path
- `uv run python scripts/checkpoint_apply.py apply --path specs/052-checkpoint-apply-pipeline/tasks.md --format text` returned the expected `mcp_local_only` manual-follow-up path
- `uv run python scripts/checkpoint_apply.py apply --path src/repo_memory/query_policy.py --lightrag-dry-run --format text` passed and confirmed the `lightrag_only` apply path
- `uv run python scripts/checkpoint_apply.py apply --path docs/context-policy.md --lightrag-dry-run --format text` passed and confirmed the `both` classification plus MCP manual-follow-up path without entity snapshots
- manual runtime investigation showed that repeated non-clean `scripts/lightrag_pilot.py build` runs previously failed on duplicate-document doc-status entries, while `build --clean` succeeded with `failed: 0` and a successful follow-up query
- the current code now plans selective incremental refresh from existing `doc_status` state: unchanged files are skipped, changed files are deleted and reinserted, new files are inserted, removed files are deleted, and stale duplicate status artifacts are cleaned up without full rebuild
- `.venv/bin/python scripts/lightrag_pilot.py build --dry-run` now reports incremental plan fields such as `delete_doc_count`, `insert_chunk_count`, `unchanged_paths`, `added_paths`, `updated_paths`, `removed_paths`, and `duplicate_cleanup_paths`
- `.venv/bin/python scripts/checkpoint_apply.py apply --path docs/context-policy.md --memory-entity-file /tmp/052-memory-entity.json --format text` passed and confirmed the full `both` apply order (`lightrag` then `mcp_memory`) with no manual follow-up
- `rg -n "Feature: 052-checkpoint-apply-pipeline" in_memory/memory.jsonl /tmp/052-memory-entity.json` confirmed that the explicit memory entity snapshot was applied into the local mirror
