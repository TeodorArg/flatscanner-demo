# Tasks: Context-Economy Workflow

## Status

- [x] Feature folder created
- [x] Canonical `spec.md` created
- [x] Canonical `plan.md` created
- [x] Canonical `tasks.md` created

## Phase 1. Freeze Architecture

- [x] Define the layered role of canonical files, MCP memory, local mirror, and `LightRAG`
- [x] Define the anti-goal that no new source of truth may be introduced
- [x] Record the architecture decision in a durable ADR

## Phase 2. Freeze Workflow Contract

- [x] Create a canonical workflow doc for context economy
- [x] Define `simple`, `feature-work`, and `deep-audit` budget profiles
- [x] Define retrieval trigger rules and bootstrap order
- [x] Define separate refresh triggers for `LightRAG` and MCP/local mirror

## Phase 3. Align Existing Canon

- [x] Review `docs/context-policy.md` for overlap or necessary narrowing
- [x] Review `docs/local-memory-sync.md` for summary-layer compatibility
- [x] Review top-level process docs for context-economy references only where useful
- [x] Add a daily-use checkpoint checklist for `LightRAG` versus MCP/local-memory refresh decisions

## Phase 4. Define Future Automation Slice

- [x] Decide whether repo bootstrap summaries should be generated manually or by helper tooling
- [x] Decide whether feature bootstrap summaries should be generated manually or by helper tooling
- [x] Identify the minimal future implementation-loop surface for automation
- [x] Open the next helper/tooling feature as a separate implementation slice

## Completion Criteria

- [x] The repository has one explicit architecture decision for context economy
- [x] The repository has one canonical workflow contract for budgeted context assembly
- [x] Canonical files remain primary and derivative layers remain subordinate
- [x] A later implementation feature can be opened without reopening the architecture discussion

## Execution Note

Any later product-code or runtime automation changes must go through the
standard isolated worktree/branch/PR loop; this planning feature is docs-first.
