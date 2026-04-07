# Evaluation: Pilot Corpus Benchmark Alignment

## Purpose

This document records the `046` coverage map and the alignment decision for the
frozen `045` benchmark.

It answers three questions:

1. which benchmark targets are supported by the current pilot policy
2. which targets are only available through mandatory-doc injection or accidental
   current-index state
3. which next strategy best preserves a clean pilot baseline while keeping the
   broader benchmark useful

## Inputs

- `specs/045-retrieval-quality-benchmark/evaluation.md`
- `specs/044-lightrag-retrieval-precision/evaluation.md`
- `docs/context-policy.md`
- `docs/lightrag-local-pilot.md`

## Baseline Constraints

### Canonical Pilot Corpus Policy

Per `docs/context-policy.md`, the current pilot corpus is intentionally small
and process-oriented.

Included by policy:

- `.specify/memory/constitution.md`
- `AGENTS.md`
- `README_PROCESS_RU.md`
- `PROCESS_OVERVIEW_EN.md`
- `DELIVERY_FLOW_RU.md`
- `docs/README.md`
- `docs/project-idea.md`

Not included by policy unless a later canonical change says otherwise:

- `docs/context-policy.md`
- `docs/ai-pr-workflow.md`
- `docs/local-memory-sync.md`
- `docs/lightrag-local-pilot.md`
- `docs/project/frontend/frontend-docs.md`
- `docs/project/backend/backend-docs.md`
- active or historical `specs/*`
- `src/`
- `tests/`

### Mandatory-Context Layer

Some files are not in the pilot corpus but can still enter the final context
pack through mandatory injection:

- `.specify/memory/constitution.md`
- `AGENTS.md`
- `docs/README.md`
- active feature docs
- `docs/ai-pr-workflow.md` for product-code or review-loop work
- conditional backend/frontend docs when the task type actually requires them

This means `046` must distinguish:

- indexed corpus coverage
- mandatory context-pack coverage
- accidental availability in the current existing `.lightrag/index`

### Current-Index Caution

`045` was executed against the existing `.lightrag/index` after a `build`
refresh failed on duplicate-document validation.

Inference:

- benchmark behavior from `045` is useful evidence
- but it is not a clean proof that the current existing index exactly matches
  the canonical pilot corpus policy

## Context7 Constraints

Context7-backed `LightRAG` notes used in this decision:

- official query modes are `naive`, `local`, `global`, `hybrid`, and `mix`
- references are returned when `include_references=True`
- `include_chunk_content` only works when references are enabled

Inference from those docs plus the repo pilot contract:

- if the repository changes the intended corpus target set, it must rerun the
  pilot indexing flow before comparing benchmark results as one baseline

## Known Aligned Baseline From `044`

`specs/044-lightrag-retrieval-precision/evaluation.md` already validates this
subset on the current pilot baseline:

- Q3 taxonomy-file precision: `PASS`
- Q4 pilot-boundary / pilot-corpus definition: `PASS`
- Q5 mandatory versus retrieve-on-demand policy: `PASS`

This subset must remain treated as proven current-baseline capability unless a
future clean rebuild disproves it.

## Coverage Map

Status meanings used below:

- `aligned`: supported by the current pilot contract without needing corpus expansion
- `partial`: mixed target set; some expected files fit the current pilot contract and some do not
- `misaligned`: the frozen benchmark expects files the current pilot does not aim to index or inject

### Per-Question Map

| Benchmark | Expected-file coverage vs policy | Mandatory-doc support | `045` result | Alignment | Likely dominant cause | Recommended track |
| --- | --- | --- | --- | --- | --- | --- |
| `BQ1` taxonomy files | Fully in current pilot corpus | Not required | `PASS` | `aligned` | retrieval/reference noise only | `Track A` |
| `BQ2` canonical read order | Core docs are in corpus; frontend/backend docs are out-of-corpus by policy | frontend/backend docs are conditional mandatory, not guaranteed for this generic benchmark row | `PARTIAL` | `partial` | mixed benchmark target set | `Track A`, but narrow the question to current-pilot read-order scope |
| `BQ3` pilot boundary and corpus definition | `docs/lightrag-local-pilot.md` is out-of-corpus; `docs/context-policy.md` is also out-of-corpus by policy even though it surfaced in observed runs | no mandatory injection for the setup-doc half | `PARTIAL` | `partial` | mixed target set plus possible current-index drift | split into boundary-only `Track A` and setup-doc `Track B` expectations |
| `BQ4` mandatory vs retrieve-on-demand | several expected files are not indexed by policy | strong mandatory injection for product-code work makes the final pack valid | `PASS` | `aligned` | answer shaping already solved in `044` | `Track A` |
| `BQ5` local-memory mirror policy | `docs/local-memory-sync.md` and `docs/context-policy.md` are out-of-corpus | no mandatory injection for this general question | `FAIL` | `misaligned` | benchmark expects docs outside the pilot target set | `Track B` |
| `BQ6` generic PR-loop contract | `docs/ai-pr-workflow.md` is out-of-corpus; `AGENTS.md` and constitution are in-corpus | review-work mandatory injection can supply `docs/ai-pr-workflow.md` | `PARTIAL` | `partial` | mixed corpus plus mandatory-policy dependence | `Track A` as a context-pack benchmark, not a pure indexed-corpus benchmark |
| `BQ7` PR-loop completion conditions | exact PR contract file is out-of-corpus | review-work mandatory injection can supply it | `PARTIAL` | `partial` | mixed corpus plus mandatory-policy dependence | `Track A` as a context-pack benchmark, with file-precision caveat |
| `BQ8` feature ownership across `042/044/045` | expected feature-memory files are out-of-corpus | no mandatory injection for unrelated feature history | `FAIL` | `misaligned` | feature-memory corpus gap | `Track B` |
| `BQ9` local pilot setup and stack | `docs/lightrag-local-pilot.md` is out-of-corpus | no mandatory injection for this general question | `PARTIAL` | `misaligned` | setup-doc corpus gap; partial score came from adjacent docs rather than target coverage | `Track B` |
| `BQ10` implementation location | `src/`, `tests/`, and supporting plan docs are out-of-corpus | no mandatory injection for code/test location | `FAIL` | `misaligned` | implementation-location corpus gap | `Track B` |

## By Class

### `taxonomy-read-order`

- Current state: `partial`
- `BQ1` is a valid current-pilot benchmark row.
- `BQ2` mixes current-pilot process-memory targets with out-of-corpus
  frontend/backend docs, so it should be narrowed if kept in the current-pilot
  track.

### `policy-boundary`

- Current state: split between `aligned` and `misaligned`
- `BQ4` is a strong current-pilot row because the pilot contract explicitly
  supports mandatory-doc injection.
- `BQ5` is outside the current pilot target set.
- `BQ3` is mixed because it asks both a current-pilot policy question and an
  out-of-corpus setup-document question.

### `workflow-pr-loop`

- Current state: `partial`
- These rows are feasible in the current context-pack contract because
  `docs/ai-pr-workflow.md` can be injected for review/product-code tasks.
- They are weak as pure indexed-corpus questions because the canonical PR-loop
  file is not part of the pilot corpus.

### `feature-memory-navigation`

- Current state: `misaligned`
- The current process-only pilot does not aim to index active or historical
  feature-memory docs.

### `architecture-system-location`

- Current state: `misaligned`
- Setup docs, implementation code, and tests are outside the current process-only
  corpus.

## Strategy Comparison

### Option A. Benchmark Narrowing Only

Assessment:

- too aggressive as the only decision
- would preserve the small pilot cleanly
- but would hide useful evidence about which broader repository-memory questions
  require corpus expansion

Decision:

- rejected as the sole strategy

### Option B. Immediate Pilot Corpus Expansion

Assessment:

- too early as the immediate decision
- would answer many current benchmark gaps
- but would also change the pilot boundary before the repository has explicitly
  decided that the small process-only baseline is no longer the canonical pilot

Decision:

- rejected as the immediate next step

### Option C. Split-Track Strategy

Assessment:

- best fit for the evidence
- preserves the validated current-pilot baseline from `044`
- keeps `045`'s broader benchmark value without pretending all rows belong to
  the same corpus contract
- exposes policy/index drift instead of burying it

Decision:

- chosen

## Chosen Direction

The repository should adopt a split-track strategy.

### Track A. Current-Pilot Benchmark

Purpose:

- measure what the current small process-memory pilot and mandatory-doc policy
  are supposed to support now

Track A rows:

- `BQ1`
- `BQ4`
- `BQ6`
- `BQ7`

Track A rows that should be narrowed or split before future scoring:

- `BQ2`: narrow to the current-pilot read-order scope instead of expecting
  frontend/backend docs
- `BQ3`: keep only the pilot-boundary/corpus-policy half here

This track explicitly preserves the `044`-validated `Q3/Q4/Q5` baseline.

### Track B. Expansion Benchmark

Purpose:

- keep the broader benchmark questions that are useful but currently outside the
  pilot target set

Track B rows:

- `BQ5`
- `BQ8`
- `BQ9`
- `BQ10`
- the setup-doc half of `BQ3`

Track B is not evidence that current ranking alone is broken. It is mainly a
candidate set for future corpus expansion.

## Follow-Up Boundary

### What `046` resolves now

- the benchmark-to-corpus mismatch is now explicit
- the preferred strategy is fixed as `split-track`
- full benchmark narrowing and immediate corpus expansion are both rejected as
  the immediate standalone move

### What still requires a later implementation loop

Any of the following must happen in a separate isolated implementation
feature/worktree/PR loop:

- changing the canonical pilot corpus policy in `docs/context-policy.md`
- changing the repo pilot indexing inputs or build flow
- changing `src/repo_memory/lightrag_pilot.py`
- changing `tests/test_lightrag_pilot.py`
- rebuilding the pilot index as the baseline for a new expanded-corpus benchmark

## Sequenced Follow-Ups

The next work should be treated as two different tasks, not one duplicated task.

### Follow-Up 1. Docs-only refinement of the `045` benchmark

Purpose:

- update the benchmark contract so `Track A` and `Track B` are explicit in the
  `045` feature memory
- narrow or split mixed rows such as `BQ2` and `BQ3`
- preserve the current-pilot baseline without changing corpus/indexing behavior

Why this is first:

- it clarifies what the repository is measuring before any corpus-expansion work
- it prevents a later implementation slice from chasing benchmark rows that have
  not yet been canonically reassigned

### Follow-Up 2. Separate implementation feature for `Track B`

Purpose:

- change corpus/indexing behavior only if the repository decides to support the
  broader out-of-corpus benchmark rows

Possible scope:

- pilot corpus policy updates
- indexing input changes
- clean rebuild and validation against the expanded target set

Why this is separate:

- it changes runtime/indexing behavior rather than only benchmark interpretation
- it depends on the docs-only refinement, but it does not duplicate it

Decision:

- these are two distinct follow-up tasks
- `Follow-Up 1` should happen first
- `Follow-Up 2` should remain recorded as the later implementation path for
  `Track B`

## Durable-Docs Decision

No durable policy change outside the `046` feature folder is required yet.

Reason:

- `046` resolves the benchmark interpretation problem first
- any actual corpus expansion should be recorded only when the repository opens
  the separate implementation slice that changes policy and/or indexing behavior
