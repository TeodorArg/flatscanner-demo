# Context-Economy Workflow

This document defines the canonical workflow for assembling repository context
under token budgets.

It builds on the existing repository rules:

- canonical truth stays in files
- MCP memory is derivative compressed recall
- local `in_memory/memory.jsonl` is a selective mirror
- `LightRAG` is a conditional retrieval accelerator

## Purpose

The repository needs one stable workflow that answers four questions:

1. what to read first
2. when to use MCP summaries
3. when to use `LightRAG`
4. when derivative layers must be refreshed

The goal is to reduce context-window cost without weakening process safety.

## Layer Order

Use layers in this order:

1. canonical files
2. MCP memory
3. local mirror
4. `LightRAG`

Interpretation:

- canonical files decide truth
- MCP memory helps start cheaply
- local mirror exists for portability and audit
- `LightRAG` helps discover and rank supporting files when manual targeting is
  too expensive

## Budget Profiles

### `simple`

Use for:

- narrow factual questions
- locating one governing rule
- quick session restart

Default workflow:

1. load only the mandatory docs required by task type
2. check MCP bootstrap facts
3. read one or two target canonical files
4. do not call `LightRAG` unless the target file is unclear

### `feature-work`

Use for:

- active feature planning
- implementation preparation
- review-loop questions for one active feature

Default workflow:

1. load mandatory core docs
2. load active `spec.md`, `plan.md`, and `tasks.md`
3. load conditional mandatory docs for the task type
4. use MCP feature bootstrap facts
5. call `LightRAG` only for supporting historical context or ambiguous file
   discovery

### `deep-audit`

Use for:

- architecture investigation
- consistency analysis
- broad historical or multi-feature reasoning

Default workflow:

1. load mandatory core docs
2. load active feature docs if applicable
3. use MCP bootstrap facts to narrow search space
4. use `LightRAG` for ranked supporting context across the indexed corpus
5. manually open canonical files that the retrieval step surfaces

## Bootstrap Summaries

### Repo Bootstrap

Preferred source:

- MCP memory

Should summarize:

- current project identity
- current repository-memory architecture boundary
- latest durable repo-wide decisions
- open durable follow-up directions

### Feature Bootstrap

Preferred source:

- MCP memory

Should summarize:

- feature purpose
- current status
- key constraints
- open follow-ups
- whether the implementation loop is complete or still in progress

### Local Mirror Role

Use `in_memory/memory.jsonl` only when:

- local offline visibility matters
- you need a portable snapshot of repo-scoped MCP entities
- you are auditing whether local parity matches MCP

Do not treat the local mirror as the primary bootstrap source when MCP is
available.

## Retrieval Trigger Matrix

### `LightRAG` is unnecessary when

- the answer should come directly from mandatory docs
- the active feature files are already known
- one canonical file is already identified
- the task is satisfied by MCP bootstrap plus one targeted file read

### `LightRAG` is recommended when

- several candidate files may answer the question
- historical feature memory may matter
- the task needs supporting references across multiple indexed documents
- manual file targeting is possible but likely slower and noisier

### `LightRAG` is required when

- ranked discovery across the indexed corpus is the actual task
- benchmarked retrieval question classes are being evaluated
- the question explicitly asks for repository-wide or corpus-wide location help

## Refresh Policy

There are two different refresh loops:

1. `LightRAG` corpus/index refresh
2. MCP/local-memory refresh

They are related, but they are not the same thing.

## LightRAG Refresh Policy

`LightRAG` should be refreshed only when indexed truth or indexing assumptions
change.

### Rebuild Or Refresh Is Required When

- the explicit corpus allowlist in `docs/context-policy.md` changes
- an indexed canonical file changes materially
- chunking rules or metadata schema change
- the embedding model changes
- `working_dir` policy changes
- indexed implementation files under the allowed `src/` or `tests/` surface
  change materially

### Rebuild Or Refresh Is Usually Recommended When

- answer-shaping or retrieval code changes in indexed pilot modules could change
  benchmark interpretation
- benchmark rows are being re-run after a completed retrieval-related feature
- a clean baseline is needed after previous index drift or failed refreshes

### Rebuild Or Refresh Is Not Required When

- only non-indexed files change
- only MCP memory changes
- only `in_memory/memory.jsonl` changes
- only broad process docs outside the current corpus change
- only query usage changes but indexed corpus and retrieval code stay the same

### Validation Without Rebuild Is Acceptable When

- the change affects workflow docs outside the pilot corpus
- the task only needs canonical doc updates and not retrieval remeasurement
- the repository is clarifying process language without touching indexed files

### Rebuild Scope Rule

If the embedding model changes, treat the index as a new baseline and do a full
rebuild.

If only indexed documents or indexed retrieval code change under the same
embedding baseline, the repository may use the canonical script-first rebuild
flow for refresh validation.

## MCP And Local-Mirror Refresh Policy

MCP and local mirror should refresh only when durable repo-scoped facts change
in canonical files.

### MCP Refresh Is Required When

- a durable architecture decision is accepted
- a feature phase or completion state is durably recorded in canonical files
- a stable repository-wide rule changes
- a durable benchmark or validation outcome should be preserved across sessions

### MCP Refresh Is Not Required When

- wording churn does not change durable meaning
- branch-local notes exist without canonical backing
- incomplete implementation work is not yet reflected in canonical files
- temporary reasoning or exploratory discussion has not become repository truth

### Local `memory.jsonl` Refresh Is Required When

- MCP was updated with repo-scoped durable facts and local parity is desired
- a repo bootstrap or feature bootstrap snapshot should remain inspectable
  offline
- a repo-scoped entity already mirrored locally has changed materially

### Local `memory.jsonl` Refresh Is Not Required When

- MCP changed only for unrelated projects or transient entities
- the new MCP facts are too noisy or too ephemeral for local parity
- no repo-scoped mirrored entity changed materially

## Operational Sequence

Use this sequence after a meaningful checkpoint:

1. update canonical files
2. decide whether the changed files are inside the indexed `LightRAG` corpus
3. if yes, decide whether rebuild or refresh validation is required
4. decide whether the checkpoint created new durable repo-scoped facts
5. if yes, update MCP memory
6. refresh local `in_memory/memory.jsonl` only if local parity remains useful

## Checkpoint Helper

The repository-local helper for this decision is:

- `scripts/checkpoint_decision.py`

This helper is read-only in v1.

It does not:

- rebuild `LightRAG`
- write MCP memory
- rewrite `in_memory/memory.jsonl`

It only classifies the checkpoint and explains the reasoning.

### When To Use It

Use it after canonical doc/spec/task updates when you want a fast,
repeatable classification of:

- whether indexed `LightRAG` truth changed
- whether durable repo-scoped facts changed
- whether local parity is worth keeping

It is most useful for daily checkpoints where the file set is already known or
easy to discover from the current working tree.

### How It Works

The helper combines:

- changed file paths supplied explicitly or discovered from `git diff`
- the current indexed allowlist from `docs/context-policy.md`
- durable-fact rules from this workflow and related canonical docs
- local mirror inspection of `in_memory/memory.jsonl` for parity hints

It then returns exactly one outcome:

- `neither`
- `lightrag_only`
- `mcp_local_only`
- `both`

### Default Interpretation

- `neither`: the change is outside the indexed corpus and does not create a new durable repo fact
- `lightrag_only`: indexed truth changed, but no durable repo-scoped fact should be synced
- `mcp_local_only`: durable repo-scoped fact changed, but indexed truth did not
- `both`: indexed truth changed and durable repo-scoped fact changed

### Example Commands

Use explicit paths for deterministic checks:

```bash
python scripts/checkpoint_decision.py decide \
  --path docs/context-policy.md
```

Use the current working-tree diff:

```bash
python scripts/checkpoint_decision.py decide --git-diff
```

If the checkpoint is wording-only or otherwise ambiguous, the helper may still
need explicit operator judgment. In that case, use the narrow override flags
instead of treating the path-based heuristic as canonical truth.

## Checkpoint Checklist

Run this checklist after any durable doc/spec/task checkpoint.

### Step 1. Did indexed corpus change?

Ask:

- did the allowlist in `docs/context-policy.md` change
- did any indexed canonical doc change materially
- did any indexed `src/` or `tests/` pilot file change materially
- did chunking, metadata, embedding, or `working_dir` policy change

If yes:

- evaluate `LightRAG` rebuild or refresh validation

If no:

- do not rebuild `LightRAG` just because other docs or memory layers changed

### Step 2. Did durable repo facts change?

Ask:

- was a durable architecture or process decision accepted
- was a feature phase or completion state durably recorded
- was a benchmark or validation result fixed in canonical files
- was a repo-scoped rule clarified in a stable way

If yes:

- update MCP memory for the durable fact

If no:

- do not update MCP for draft churn or temporary reasoning

### Step 3. Do we need local parity?

Ask:

- is the changed repo-scoped entity mirrored locally already
- would offline audit or local inspection benefit from parity
- is the MCP update durable and selective enough to keep locally

If yes:

- refresh `in_memory/memory.jsonl`

If no:

- skip local mirror refresh

### Step 4. Final action outcome

Choose one of:

- `neither`
- `LightRAG only`
- `MCP/local sync only`
- `both`

Default interpretation:

- indexed-truth change only: usually `LightRAG only`
- durable-fact change only: usually `MCP/local sync only`
- both indexed-truth and durable-fact change: `both`
- draft or non-indexed wording change only: `neither`

## Decision Table

### Example: feature tasks completed, docs/specs updated, indexed files unchanged

- `LightRAG`: no rebuild required
- MCP: update if the completion facts are durable
- local mirror: update if the feature is mirrored locally

### Example: `docs/context-policy.md` allowlist changed

- `LightRAG`: rebuild required
- MCP: update if the corpus-policy decision is durable
- local mirror: update if the project entity or related feature entity is
  mirrored locally

### Example: `src/repo_memory/*.py` indexed pilot modules changed

- `LightRAG`: refresh or rebuild validation required
- MCP: update only if the canonical feature memory records durable outcomes
- local mirror: update only after MCP changes

### Example: only `in_memory/memory.jsonl` was repaired

- `LightRAG`: no action
- MCP: no action unless canonical correction required it
- local mirror: yes, but this is a formatting/parity repair, not a durable
  repository-memory event

## Relationship To Existing Canon

- `docs/context-policy.md` defines what is mandatory and what is in the current
  pilot corpus
- `docs/local-memory-sync.md` defines the write order and parity rules
- this document defines the higher-level workflow and refresh triggers that tie
  those policies together

## References

- `docs/context-policy.md`
- `docs/local-memory-sync.md`
- `docs/lightrag-local-pilot.md`
- `docs/adr/005-layered-context-economy.md`
