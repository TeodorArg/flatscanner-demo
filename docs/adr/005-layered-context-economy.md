# ADR 005: Layered Context Economy

## Status

Accepted

## Context

The repository already has:

- canonical repository memory in files
- derivative MCP memory and local mirror policy
- a benchmarked `LightRAG` pilot

But without one explicit architecture decision, agents can still waste context
window by:

- reading too many files too early
- treating derivative memory as a competing truth layer
- invoking retrieval when targeted file reads would be cheaper

The project needs one durable cross-feature rule for how context should be
assembled under token budgets.

## Decision

Use a layered context-economy model.

### Layer 1. Canonical truth

- `docs/`
- `specs/<feature-id>/`
- `.specify/`
- `AGENTS.md` and other canonical process files

These remain the only source of truth.

### Layer 2. Compressed durable recall

- MCP memory

This layer stores repo-scoped durable facts that help future sessions start
cheaply, but it must only summarize facts already recorded in canonical files.

### Layer 3. Local operational mirror

- `in_memory/memory.jsonl`

This layer is a selective local mirror of repo-relevant MCP entities for
inspection, portability, and offline audit. It is not a canonical knowledge
layer and is not the default retrieval source.

### Layer 4. Conditional retrieval accelerator

- `LightRAG`

This layer exists to reduce file-discovery cost when the target files are not
obvious or when supporting context must be ranked across an indexed subset. It
must remain subordinate to mandatory canonical docs and benchmarked against the
current corpus policy.

## Consequences

- The repository keeps files as truth and summaries as derivative helpers.
- MCP memory becomes the primary cheap bootstrap layer across sessions.
- Local `memory.jsonl` stays small and selective rather than exhaustive.
- `LightRAG` is used conditionally, not by default for every task.
- The operational workflow canon for this layered model lives in
  `docs/context-economy-workflow.md`.
- Future workflow docs may define budget profiles such as `simple`,
  `feature-work`, and `deep-audit`, but they must follow this layer order.
