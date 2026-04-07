# Plan: Context-Economy Workflow

## Goal

Зафиксировать постоянную architecture + workflow contract для дешевого и
воспроизводимого context assembly, не ломая существующее правило
`files are canonical`.

## Strategy

Новая фича должна не "добавить еще один memory layer", а упорядочить уже
существующие слои в одну рабочую модель:

1. canonical files as truth
2. MCP memory as compressed durable recall
3. local `memory.jsonl` as selective mirror
4. `LightRAG` as conditional retrieval accelerator

Главная цель этой фичи не retrieval quality сама по себе, а уменьшение среднего
контекстного окна без потери process safety.

## Working Hypothesis

Наибольшую экономию токенов дает не новый storage, а policy-driven context
assembly:

- маленький mandatory core
- feature-scoped reads instead of broad repo reads
- compact MCP bootstrap summaries
- conditional retrieval only when targeting files manually is too expensive

Следовательно в первую очередь нужно зафиксировать:

- architectural roles
- bootstrap policy
- budget profiles
- retrieval trigger policy

а уже потом решать, нужен ли отдельный helper automation layer.

## Target Durable Outputs

### Output 1. ADR for layered context economy

Нужен durable cross-feature architecture decision в `docs/adr/`, который
зафиксирует:

- canonical truth stays in files
- MCP is the primary compressed recall layer
- local mirror is operational, not canonical
- `LightRAG` is conditional and benchmarked

### Output 2. Canonical workflow doc

Нужен dedicated workflow/policy doc in `docs/`, который опишет:

- context-budget profiles
- bootstrap order
- retrieval trigger matrix
- cold/hot artifact policy

### Output 3. Feature memory

Feature memory in `specs/050-context-economy-workflow/` должна:

- зафиксировать scope and boundaries
- разложить работу на doc-first phases
- отделить workflow canon from later tooling implementation

## Proposed Budget Profiles

### Profile 1. `simple`

Use for:

- narrow factual questions
- locating one rule or one file
- quick session restart

Default pack:

- mandatory core docs only when needed by task type
- MCP bootstrap facts first
- no retrieval unless the target file is unclear

### Profile 2. `feature-work`

Use for:

- active feature planning
- implementation prep
- review-loop decisions for one active feature

Default pack:

- mandatory core docs
- active `spec.md`, `plan.md`, `tasks.md`
- conditional mandatory docs
- MCP feature summary
- retrieval only for supporting historical or subsystem context

### Profile 3. `deep-audit`

Use for:

- architecture investigation
- broad consistency analysis
- multi-feature historical reasoning

Default pack:

- mandatory core docs
- active feature if present
- broader retrieved support
- explicit allowance for ADRs, related historical features, and implementation
  references

## Retrieval Trigger Matrix

### Retrieval is unnecessary when

- the answer should come directly from mandatory docs
- the active feature files are clearly known
- the question is about one already-identified canonical file

### Retrieval is recommended when

- multiple candidate files may answer the question
- related historical feature memory may matter
- the task needs supporting references across docs/specs/code

### Retrieval is required when

- the task explicitly depends on ranked discovery across the indexed corpus
- benchmarked question classes are known to benefit from retrieval
- manual file targeting would likely be more expensive than retrieval plus
  verification

## Bootstrap Summary Model

The workflow should define two compact summary units.

### Unit 1. Repo Bootstrap

Should capture:

- current project identity
- latest durable repo-wide decisions
- current retrieval/memory architecture boundary
- active durable follow-up directions

### Unit 2. Feature Bootstrap

Should capture:

- feature purpose
- current status
- key constraints
- open follow-ups
- whether product-code loop is complete or still in progress

These units should prefer MCP memory and only mirror locally when durable,
repo-scoped, and worth auditing offline.

## Execution Phases

### Phase 1. Freeze architecture

Deliver:

- ADR for layered context economy
- shared vocabulary for truth, summary, mirror, retrieval, and budget profile

### Phase 2. Freeze workflow canon

Deliver:

- canonical workflow doc in `docs/`
- profile definitions
- retrieval trigger matrix
- bootstrap order

### Phase 3. Align process docs

Review whether these docs need narrow updates after the new canon exists:

- `docs/README.md`
- `README_PROCESS_RU.md`
- `PROCESS_OVERVIEW_EN.md`
- `AGENTS.md`
- `docs/context-policy.md`
- `docs/local-memory-sync.md`

### Phase 4. Define automation follow-up

Identify the smallest future implementation slice, such as:

- helper for generating repo bootstrap summaries
- helper for generating feature bootstrap summaries
- policy-aware context-pack preset handling

This phase should define later product-code scope without implementing it in the
main checkout.

## Touched Areas

Docs-first surface for this feature:

- `specs/050-context-economy-workflow/spec.md`
- `specs/050-context-economy-workflow/plan.md`
- `specs/050-context-economy-workflow/tasks.md`
- `docs/adr/005-layered-context-economy.md`
- later likely `docs/context-economy-workflow.md`

Possible later implementation-loop surface:

- `src/repo_memory/`
- `scripts/`
- tests for context-pack presets or summary helpers

## Risks

### R1. Summary-layer creep

The repository could accidentally introduce a new quasi-canonical summary layer
instead of keeping summaries derivative.

### R2. Over-engineered retrieval triggers

If the trigger matrix becomes too complex, agents will ignore it and return to
manual broad reading.

### R3. Canon drift across docs

If the new workflow doc, `context-policy`, and `local-memory-sync` disagree, the
whole context-economy model becomes self-defeating.

## Validation Plan

Success for this planning feature requires:

1. durable architecture decision is accepted
2. workflow canon is clearly scoped
3. future implementation is separated from doc-first planning
4. no new source of truth is introduced by the design
