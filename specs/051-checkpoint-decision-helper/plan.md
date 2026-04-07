# Plan: Checkpoint Decision Helper

## Goal

Реализовать минимальный read-only helper, который автоматизирует canonical
checkpoint decision без автоматического rebuild/sync side effects.

## Strategy

The helper should answer one narrow operational question:

- after this checkpoint, do we need `LightRAG`, MCP/local sync, both, or neither

It should not automate downstream actions yet.

## Working Hypothesis

Most manual overhead is not in performing rebuild or sync, but in deciding
which action class applies.

If the helper:

- reads the current canonical policy
- inspects changed files
- evaluates durable-fact triggers
- prints one decision plus reasoning

then the repository gets most of the daily operational benefit without opening
automation-risk around accidental writes.

## Expected Interface

Canonical helper shape for v1:

- repository-local command under `scripts/`
- read-only execution
- machine-readable decision plus human-readable reasoning

Example outcome shape:

- `decision`: `neither | lightrag_only | mcp_local_only | both`
- `indexed_corpus_changed`: `true/false`
- `durable_repo_facts_changed`: `true/false`
- `local_parity_recommended`: `true/false`
- `reasons`: list of matched triggers

## Proposed Inputs

### Input mode 1. Explicit path list

Useful for deterministic tests and scripted validation.

### Input mode 2. Current changed-file discovery

Useful for day-to-day operation from the working tree.

The implementation feature should choose one canonical default and may support
the other as an explicit mode.

## Proposed Implementation Surface

Likely files:

- `scripts/` helper entrypoint
- maybe `src/repo_memory/` or a narrow policy module if shared logic is needed
- tests covering the scenario matrix

The implementation should avoid spreading logic across many files unless reuse
is clearly justified.

## Scenario Matrix

### Scenario A. Indexed-surface change only

Expected decision:

- `lightrag_only`

### Scenario B. Durable-fact change only

Expected decision:

- `mcp_local_only`

### Scenario C. Indexed-surface change plus durable-fact change

Expected decision:

- `both`

### Scenario D. Draft or non-indexed wording change only

Expected decision:

- `neither`

### Scenario E. MCP/local parity not useful

Expected decision:

- still decide on MCP update if durable facts changed, but local refresh may be
  reported as unnecessary

## Execution Phases

### Phase 1. Freeze helper contract

Deliver:

- canonical input/output contract
- decision enum
- scenario matrix

### Phase 2. Open isolated implementation loop

Deliver:

- implementation worktree/branch/PR
- read-only helper command

### Phase 3. Validate scenario matrix

Deliver:

- automated tests for representative cases
- example outputs for the repo workflow

## Risks

### R1. Policy duplication drift

If helper logic duplicates the docs too rigidly, it may drift when the docs
change.

### R2. Overreach into write automation

The implementation may try to rebuild or sync directly, which is out of scope
for v1.

### R3. Ambiguous durable-fact detection

Some changes may still require human judgment; the helper should expose this
rather than pretend certainty where the canonical docs do not provide it.

## Validation Plan

Success requires:

1. a small, reviewable helper surface
2. stable scenario outputs
3. no repository writes in v1
4. alignment with the canonical workflow docs
