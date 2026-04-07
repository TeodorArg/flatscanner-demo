# Plan: Post-047 Retrieval Quality Tuning

## Goal

Улучшить retrieval quality на post-`047` expanded baseline только через
доступные non-model корректировки: query-time tuning, reference fidelity и
deterministic file-first answer shaping.

## Baseline Inputs

Этот feature стартует из уже зафиксированного состояния:

- `044` закрыл Q3/Q4/Q5 precision regressions на узком baseline
- `046` развёл Track A и Track B
- `047` закрыл Track B corpus expansion и clean rebuild
- после `047` дальнейшие quality gaps больше нельзя трактовать как raw
  corpus-mismatch

## Working Hypothesis

Следующие улучшения можно получить без смены model stack, если сфокусироваться
на:

- per-question or per-class query parameter tuning
- stricter reference-path extraction and filtering
- file-first answer shaping, опирающемся на canonical references

## Constraints

Жёсткие ограничения для `048`:

- не менять generation model
- не менять embedding model
- не включать `rerank`
- не делать broad chunking refactor
- не делать broad extraction cleanup
- не менять corpus allowlist

## Candidate Tuning Surface

Context7-backed LightRAG knobs, которые допустимо использовать:

- `QueryParam.top_k`
- `QueryParam.chunk_top_k`
- `QueryParam.max_entity_tokens`
- `QueryParam.max_relation_tokens`
- `QueryParam.max_total_tokens`
- `include_references=True`
- narrow `user_prompt` or response-format shaping

Repository-local shaping surface:

- stricter canonical path extraction from retrieved references
- per-question file-first formatting helpers
- suppression of invented or weakly-supported file mentions
- narrow benchmark-specific heuristics if they stay explicit and test-backed

## Analysis Phases

### Phase 1. Freeze residual targets

Use post-`047` evidence to define the smallest worthwhile benchmark subset for
this tuning pass.

Deliverables:

- frozen residual question set
- expected canonical files per question
- explicit reason each question still belongs in `048`

Frozen residual subset for `048`:

- `BQ2`:
  - question: `What is the canonical read order before implementation work`
  - reason: `045` left this row at `PARTIAL` because answers drifted into a
    workflow sequence instead of naming the current-pilot anchor files from
    `AGENTS.md`
- `BQ3A`:
  - question: `Which files define the current LightRAG pilot boundary and pilot corpus policy`
  - reason: `045` left this row at `PARTIAL`; after the first `048` tuning pass,
    this remains the only still-observed drift because answers can still prefer
    setup/process docs over `docs/context-policy.md`
- `BQ6`:
  - question: `Which docs define the generic PR-loop contract for implementation and review`
  - reason: `045` left this row at `PARTIAL` because retrieval preferred broad
    process docs over `docs/ai-pr-workflow.md`
- `BQ7`:
  - question: `What conditions must be true before an orchestrated PR loop is considered done`
  - reason: `045` left this row at `PARTIAL` because one mode omitted the final
    human-approval condition and file precision stayed weak

### Phase 2. Compare allowed levers

For each residual question, identify the smallest likely effective lever:

- query parameter tuning
- reference-path filtering
- answer shaping
- narrow preprocessing rule

Reject any candidate that effectively becomes:

- model change
- `rerank`
- corpus change
- broad extraction/chunking refactor

Selected `048` levers:

- file-first `user_prompt` additions for read-order and PR-loop questions
- canonical answer shapers for read-order, PR-loop contract, PR-loop completion,
  and pilot-boundary rows
- narrow `QueryParam` tuning with `top_k`, `chunk_top_k`, and `response_type`
  for the frozen residual subset
- retrieved-document ordering that keeps canonical policy docs ahead of noisy
  extracted references for the pilot-boundary row

### Phase 3. Implementation loop

Expected implementation surface in the later isolated PR loop:

- `src/repo_memory/lightrag_pilot.py`
- `tests/test_lightrag_pilot.py`
- optionally `scripts/lightrag_pilot.py` if query wiring needs a narrow update

### Phase 4. Validation rerun

Re-run the frozen residual subset on the fixed expanded baseline and record:

- answer correctness
- canonical file precision
- reference fidelity
- remaining failure type

### Phase 5. Post-048 classification

If failures remain, classify them as one of:

- likely model-quality limit
- likely `rerank` candidate
- likely broader extraction/chunking candidate
- likely benchmark wording issue

## Touched Areas

Feature memory:

- `specs/048-post-047-retrieval-quality-tuning/spec.md`
- `specs/048-post-047-retrieval-quality-tuning/plan.md`
- `specs/048-post-047-retrieval-quality-tuning/tasks.md`
- `specs/048-post-047-retrieval-quality-tuning/evaluation.md`

Expected implementation area for the separate PR loop:

- `src/repo_memory/lightrag_pilot.py`
- `tests/test_lightrag_pilot.py`
- maybe `scripts/lightrag_pilot.py`

## Validation Plan

Success for this feature requires:

1. the residual benchmark slice is explicit
2. all applied levers stay within the non-model scope
3. file-first/reference-fidelity metrics improve on the chosen slice
4. the next follow-up boundary becomes clearer, not blurrier

## Risks

### R1. Hidden scope creep

Small retrieval tuning can drift into corpus or extraction redesign unless the
feature keeps a strict change budget.

### R2. Benchmark overfitting

Question-specific shaping can become too bespoke if not anchored to canonical
file/reference fidelity.

### R3. Weak attribution

If multiple levers are changed at once, it may become hard to tell what
actually improved the result.

## Implementation Boundary

This feature is expected to require product-code changes, so execution must use
the standard isolated implementation loop. Main-checkout docs/specs define the
scope but do not complete the feature.
