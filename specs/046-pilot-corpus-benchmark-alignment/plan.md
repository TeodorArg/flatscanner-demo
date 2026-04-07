# Plan: Pilot Corpus Benchmark Alignment

## Goal

Сделать benchmark contract and pilot corpus policy mutually consistent before
opening the next retrieval implementation slice.

## Baseline

Input baseline is the completed broader benchmark in
`specs/045-retrieval-quality-benchmark/evaluation.md`.

`046` also inherits the already-validated precision subset from
`specs/044-lightrag-retrieval-precision/evaluation.md`:

- Q3 taxonomy-file precision is `PASS`
- Q4 pilot-boundary / pilot-corpus definition is `PASS`
- Q5 mandatory-versus-retrieve-on-demand policy is `PASS`

This means the new alignment analysis must not erase the distinction between:

- process/policy questions already proven workable on the current baseline
- broader benchmark classes that fail because they expect files outside the
  current pilot corpus

The dominant result from `045` is:

- policy questions centered on `docs/context-policy.md` are the strongest
- failures cluster where benchmark expects files not present in the current
  pilot corpus
- the biggest gaps are feature-memory navigation, local-memory mirror policy,
  setup documentation, and implementation-location questions

## Working Hypothesis

The current retrieval baseline is being judged against a target set that is
broader than the current pilot corpus by design.

This means some `045` failures are not evidence that ranking is wrong; they are
evidence that corpus policy and benchmark scope are currently misaligned.

## Analysis Phases

### Phase 1. Freeze the alignment input set

Use the frozen `045` benchmark and current `docs/context-policy.md` pilot-corpus
policy as the only baseline inputs.

Deliverables:

- current included pilot files
- current explicitly excluded files
- benchmark expected-file matrix

### Phase 2. Build the coverage map

For each benchmark class and benchmark question:

- list the expected canonical files
- mark each file as in-corpus or out-of-corpus
- classify the question as:
  - aligned
  - partially aligned
  - misaligned

Initial hypotheses from `045`:

- aligned: the `044`-validated Q3/Q4/Q5 subset and policy-boundary questions
  centered on `docs/context-policy.md`
- partially aligned: taxonomy/read-order and workflow questions
- misaligned: feature-memory navigation and architecture/system-location

### Phase 3. Compare alignment strategies

Evaluate three candidate strategies.

#### Option A. Narrow benchmark to current corpus

Pros:

- preserves the original small-pilot goal
- keeps evaluation focused on current indexed scope
- avoids premature corpus expansion

Cons:

- removes some practically useful questions from the benchmark
- reduces pressure to validate feature-memory or implementation-location recall

#### Option B. Expand pilot corpus to the benchmark target set

Pros:

- makes the broader benchmark a real retrieval target
- tests richer repository-memory navigation

Cons:

- changes the pilot's boundary and noise profile
- may require indexing/build changes and fresh evaluation runs
- risks mixing corpus-expansion work with ranking work

#### Option C. Split the benchmark into two tracks

Track 1:

- current-corpus benchmark

Track 2:

- expanded-corpus benchmark

Pros:

- preserves pilot-baseline comparability
- makes out-of-corpus failures explicit instead of ambiguous

Cons:

- increases evaluation and maintenance complexity

### Phase 4. Choose the recommended direction

The recommendation must state:

- which option is preferred now
- why it is preferred over the other options
- how the chosen option preserves the already-validated `044` baseline
- whether the recommendation requires:
  - only doc/spec changes
  - or a separate implementation feature/worktree loop

### Phase 5. Define the next execution boundary

If the chosen option implies changes to:

- `docs/context-policy.md`
- pilot corpus indexing inputs
- `src/repo_memory/lightrag_pilot.py`
- `tests/test_lightrag_pilot.py`
- build/rebuild flow

then the plan must state whether the next slice is:

- docs-only alignment closure
- or a new implementation feature to execute in an isolated worktree/PR loop

## Touched Areas

- `specs/046-pilot-corpus-benchmark-alignment/spec.md`
- `specs/046-pilot-corpus-benchmark-alignment/plan.md`
- `specs/046-pilot-corpus-benchmark-alignment/tasks.md`
- `specs/046-pilot-corpus-benchmark-alignment/evaluation.md`
- optional durable docs only if the alignment decision itself is recorded as
  canonical policy

## Decision Snapshot

Current `046` decision:

- choose `split-track` rather than full benchmark narrowing or immediate pilot
  corpus expansion
- preserve the `044`-validated current-pilot baseline as `Track A`
- keep broader out-of-corpus benchmark rows as `Track B` candidates for a later
  corpus/indexing implementation slice

## Validation Plan

Success for this feature requires:

1. every `045` benchmark class has an explicit corpus-alignment status
2. the `044`-validated Q3/Q4/Q5 subset remains explicitly recognized as the
   current aligned baseline
3. the dominant failure patterns are re-labeled as corpus, retrieval, or answer
   shaping issues
4. the repository has one preferred alignment strategy
5. the next step clearly says whether product-code work is required

## Risks

### R1. Hidden policy drift

Corpus expansion may silently change the intent of the original pilot if the
policy is not updated explicitly.

### R2. Benchmark backfilling

Narrowing the benchmark too aggressively may erase useful evidence instead of
clarifying scope.

### R3. Mixed follow-up scopes

If doc-policy change and product-code change are bundled together, the next
implementation slice will be hard to review and validate.

## Candidate Follow-Ups

- doc-only update to `docs/context-policy.md` if the chosen strategy changes the
  canonical pilot corpus policy
- a new implementation feature to update corpus inputs, indexing behavior, or
  retrieval validation automation
- a later ranking-oriented feature only after corpus alignment is no longer the
  dominant blocker
