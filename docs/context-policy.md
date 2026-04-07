# Repository Context Policy

This document defines how repository context is assembled for planning,
implementation, review, and future retrieval tooling.

## Purpose

The repository must not rely on retrieval alone to decide which governing
documents are important.

This policy fixes three things:

1. the mandatory context set
2. the retrieve-on-demand set
3. the pilot corpus policy for the initial `LightRAG` rollout

## Core Rule

Repository files remain canonical.

Retrieval may reduce context load, but it must not remove required process
constraints from the context pack.

Local `in_memory/memory.jsonl` and MCP memory may help recall or inspection, but
they do not override canonical repository files and are not part of the default
mandatory context set unless a later policy says otherwise.

## 1. Mandatory Context

These documents are always part of the context pack before product-code work,
process changes, or review-loop decisions.

### Always-Read Core

- `.specify/memory/constitution.md`
- `AGENTS.md`
- `docs/README.md`

### Feature-Scoped Mandatory Set

If the task belongs to an active feature, also include:

- `specs/<feature-id>/spec.md`
- `specs/<feature-id>/plan.md`
- `specs/<feature-id>/tasks.md`

### Conditional Mandatory Docs

Add these when the task type requires them:

- `docs/ai-pr-workflow.md` for product-code work, PR-loop changes, review-loop
  questions, or merge-readiness checks
- `docs/project-idea.md` for product-framing, repository identity, or scope
  questions
- `docs/project/frontend/frontend-docs.md` when frontend implementation or
  frontend architecture is affected
- `docs/project/backend/backend-docs.md` when backend implementation or backend
  architecture is affected

## 2. Retrieve-On-Demand Context

These artifacts are not read by default for every task, but may be pulled in by
search, retrieval, or direct need.

### Durable Docs

- `docs/adr/*.md`
- `docs/glossary.md`
- other durable docs in `docs/` that refine one subsystem or workflow

### Historical Feature Memory

- closed or unrelated `specs/*/spec.md`
- closed or unrelated `specs/*/plan.md`
- closed or unrelated `specs/*/tasks.md`

### Concrete Vendor Examples

- `docs/claude-worker-orchestration.md`
- `docs/claude-pr-playbook.md`
- other agent-specific or vendor-specific example docs

### Temporary Or Draft Material

- root-level migration drafts
- exploratory notes
- historical archives

These may help investigation, but they do not override mandatory canonical docs.

## 3. Context-Pack Assembly Order

The final context pack is assembled in this order:

1. mandatory core docs
2. active feature docs, if the task is feature-scoped
3. conditional mandatory docs for the task type
4. retrieved documents ranked for the current question
5. optional human-requested or orchestrator-requested additions

If a retrieved document conflicts with a mandatory doc, the mandatory doc wins.

## 4. Pilot Corpus Policy

The current `LightRAG` pilot baseline uses a small explicit allowlist.

It still prioritizes process-memory retrieval, but it now carries the minimal
`Track B` expansion required to benchmark local pilot setup, local-memory
mirror policy, selected feature ownership history, and current implementation
location.

### Included In Pilot Corpus

Core process-memory set:

- `.specify/memory/constitution.md`
- `AGENTS.md`
- `README_PROCESS_RU.md`
- `PROCESS_OVERVIEW_EN.md`
- `DELIVERY_FLOW_RU.md`
- `docs/README.md`
- `docs/project-idea.md`

Minimal `Track B` expansion set:

- `docs/context-policy.md`
- `docs/lightrag-local-pilot.md`
- `docs/local-memory-sync.md`
- `specs/042-repo-memory-platform-lightrag/spec.md`
- `specs/042-repo-memory-platform-lightrag/plan.md`
- `specs/042-repo-memory-platform-lightrag/evaluation.md`
- `specs/044-lightrag-retrieval-precision/spec.md`
- `specs/044-lightrag-retrieval-precision/evaluation.md`
- `specs/045-retrieval-quality-benchmark/spec.md`
- `src/repo_memory/lightrag_pilot.py`
- `src/repo_memory/pilot_config.py`
- `src/repo_memory/pilot_types.py`
- `src/repo_memory/markdown_chunks.py`
- `src/repo_memory/query_policy.py`
- `src/repo_memory/reference_resolution.py`
- `src/repo_memory/lightrag_runtime.py`
- `src/repo_memory/context_pack.py`
- `tests/test_lightrag_pilot.py`

Benchmark justification for this expansion:

- `BQ3B` and `BQ9`: `docs/lightrag-local-pilot.md` plus `docs/context-policy.md`
- `BQ5`: `docs/local-memory-sync.md` plus `docs/context-policy.md`
- `BQ8`: selected `specs/042`, `specs/044`, and `specs/045` files
- `BQ10`: current pilot facade, helper implementation modules, and tests, with
  supporting canon from `docs/lightrag-local-pilot.md` and
  `specs/042-repo-memory-platform-lightrag/plan.md`

### Explicitly Excluded From Pilot Corpus

- all other `src/` files outside the explicit allowlist above
- all other `tests/` files outside the explicit allowlist above
- runtime setup files
- `docs/project/backend/backend-docs.md`
- `docs/project/frontend/frontend-docs.md`
- `docs/adr/*.md`
- `docs/ai-pr-workflow.md`
- vendor-specific example docs such as Claude-specific playbooks
- root-level drafts such as `LIGHTRAG_MIGRATION_PLAN_RU.md`
- legacy domain-specific `flatscanner` specs or docs
- unrelated active or historical feature folders outside the explicit allowlist

The point of the pilot is still to avoid repo-wide indexing. Corpus growth must
stay explicit, benchmark-justified, and minimal.

## 5. Metadata Expectations For Retrieval

Each indexed chunk should preserve at least:

- file path
- document class
- heading path
- feature id when applicable
- language

Language is metadata, not a reason to drop a chunk from the pilot corpus.

## 6. Safety Rules

- Mandatory docs must be injected even if retrieval returns nothing useful.
- Retrieval must not be treated as permission to skip the active feature folder.
- Historical and draft artifacts cannot silently replace active canonical docs.
- Corpus expansion happens only after the pilot demonstrates useful,
  low-noise retrieval on the core process-memory set.

## 7. Phase-3 Decision Summary

- Mandatory context is explicit and file-based.
- Retrieved context is additive and subordinate to mandatory docs.
- The pilot corpus is intentionally small, explicit, and benchmark-scoped.
- Legacy `flatscanner` artifacts are excluded from the pilot until later cleanup
  phases.
