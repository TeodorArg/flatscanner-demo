# Local Memory Sync Policy

This document defines the role of local `in_memory/memory.jsonl` and how it
relates to MCP memory and canonical repository files.

## Purpose

The repository already has canonical memory layers in files:

- `docs/`
- `specs/<feature-id>/`
- `.specify/`

Local `in_memory/memory.jsonl` exists for portability, inspection, and local
snapshotting of MCP memory state. It is not a fourth canonical source-of-truth
layer.

## Status Of Each Memory Layer

- `docs/`, `specs/<feature-id>/`, and `.specify/` are canonical repository
  memory
- MCP memory is a derivative working memory layer used to speed up context
  recall across sessions
- `in_memory/memory.jsonl` is a local derivative mirror of repo-relevant MCP
  memory

If there is any conflict, canonical repository files win.

## Canonical Local File

The local mirror file is:

- `in_memory/memory.jsonl`

It should be treated as a machine-friendly snapshot, not as a human-authored
primary design doc.

## JSONL Schema

Each line represents one entity snapshot in JSON.

Required fields:

- `name`: stable entity name
- `entityType`: high-level entity class such as `project`, `feature`, `doc`, or
  `decision`
- `observations`: array of stable factual statements

Current canonical local shape:

```json
{"name":"Project: flatscanner-demo repo-memory migration","entityType":"project","observations":["..."]}
```

## Schema Rules

- One entity per line
- ASCII by default unless the content itself requires another language
- `observations` should contain durable factual statements, not speculative
  notes
- The file may be rewritten from MCP memory during sync; do not rely on manual
  line ordering as meaning

## What Belongs In MCP Memory

Store repo-scoped, durable, retrieval-useful facts such as:

- stable project identity and migration status
- fixed process or architecture decisions
- completion facts for major phases
- durable constraints that are useful across future sessions

Do not treat MCP memory as the primary home for:

- temporary reasoning traces
- branch-local scratch notes
- partial draft wording that still belongs in a spec or doc
- product truth that has not yet been written into canonical files

## What Belongs In `in_memory/memory.jsonl`

Mirror only repo-relevant MCP entities that are worth keeping locally, such as:

- current project entity
- active migration or platform entities
- stable review or policy entities when they are reused across sessions

The local file does not need to mirror every transient MCP node.

## Write Order

When a durable decision is made, use this order:

1. update canonical repository files first
2. update MCP memory for the durable fact if future retrieval will benefit
3. sync `in_memory/memory.jsonl` from MCP memory when local parity is desired

This preserves the rule that files remain canonical and memory layers remain
derivative.

## Checkpoint Sync Rule

After each completed phase checkpoint or durable decision checkpoint, the
orchestrator should explicitly evaluate whether new repo-scoped durable facts
were added to canonical files.

If yes:

1. add the durable fact to MCP memory when it is likely to help future
   retrieval or cross-session recall
2. sync `in_memory/memory.jsonl` when local parity remains useful

If no:

- do not create a memory update just because files changed

Typical triggers for evaluation:

- a phase is marked complete in `specs/<feature-id>/tasks.md`
- a new durable rule is fixed in `docs/`, `spec.md`, or `plan.md`
- a canonical process or architecture decision is clarified

Non-triggers:

- draft wording churn
- branch-local scratch edits
- temporary exploratory notes
- incomplete implementation work that is not yet reflected as stable canonical
  truth

## Parity Rules

Keep MCP memory and local `memory.jsonl` in parity when all of these are true:

- the entity is repo-scoped
- the observations are durable
- the facts have already been recorded in canonical files
- local offline visibility or auditability is useful

Do not force parity for:

- ephemeral session notes
- exploratory branches of reasoning
- entities unrelated to this repository
- high-churn scratch entities that would create noise

## Manual Editing Rules

- Prefer syncing from MCP memory instead of hand-editing `memory.jsonl`
- Manual local edits are allowed only to repair formatting or restore parity
- If a local line and MCP memory disagree, reconcile against canonical files
  first, then update MCP memory, then refresh the local snapshot

## Recommended Manual Tool

The repository-local helper is:

- `scripts/sync_memory.py`

Recommended commands:

```bash
python scripts/sync_memory.py validate
python scripts/sync_memory.py upsert \
  --name "Project: flatscanner-demo repo-memory migration" \
  --entity-type project \
  --observation "Phase 5 chunking rules were documented."
python scripts/sync_memory.py remove-observation \
  --name "Project: flatscanner-demo repo-memory migration" \
  --observation "Phase 5 chunking rules were documented."
python scripts/sync_memory.py delete-entity \
  --name "Project: obsolete-local-memory-node"
```

You may also pass a full entity snapshot with `--json-file` when updating many
observations at once.

Current helper coverage:

- `validate`
- `upsert`
- `remove-observation`
- `delete-entity`

## Recommended Sync Unit

The default sync unit is one complete entity snapshot at a time, not
observation-by-observation patching across many entities.

That keeps local snapshots easy to inspect and replace.

## Relationship To Retrieval

`in_memory/memory.jsonl` is not part of the initial `LightRAG` pilot corpus
unless a later policy explicitly includes it.

The Phase 1 to Phase 4 repo-memory migration still treats Markdown files as the
canonical knowledge base for retrieval design.

## Current Repo Decision

For this repository:

- local `in_memory/memory.jsonl` is a derivative mirror, not canonical memory
- canonical truth remains in Markdown files
- MCP memory may be richer than the local mirror
- local parity is selective and repo-scoped, not exhaustive
- durable checkpoint completion should prompt an explicit memory-sync decision,
  but not every file edit should create a memory update
