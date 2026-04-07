# Spec: LightRAG Pilot Structural Refactor

## Feature ID

- `049-lightrag-pilot-structural-refactor`

## Summary

Открыть отдельную structural-refactor фичу для
`src/repo_memory/lightrag_pilot.py`, чтобы разделить текущий монолитный модуль
на небольшие подсистемы без изменения публичного entrypoint, retrieval
semantics, corpus policy или LightRAG runtime contract.

## Problem

После `047` и `048` в `src/repo_memory/lightrag_pilot.py` накопилась смешанная
логика нескольких разных подсистем:

- canonical policy constants and corpus data
- dataclass types
- Markdown preprocessing and chunking
- query classification and answer shaping
- reference extraction and fallback resolution
- LightRAG runtime wiring
- context-pack orchestration
- CLI facade

При текущем размере модуль уже превысил безопасную границу локальной
поддерживаемости и осложняет:

- reviewability
- точечные follow-up changes
- тестовую изоляцию
- понимание того, где заканчивается repo policy и начинается retrieval logic

Проблема не в самой integration strategy. Context7-backed official LightRAG
docs подтверждают, что текущие базовые инварианты корректны:

- programmatic `LightRAG(...)` integration допустима
- локальный `working_dir` допустим как storage root
- `initialize_storages()` и `finalize_storages()` обязательны
- `QueryParam` с `mode`, `top_k`, `chunk_top_k`, `response_type`, и
  `include_references` допустим для script-first local integration

Следовательно следующий срез должен быть structural cleanup, а не новый runtime
или retrieval-behavior redesign.

## Goal

После завершения этой фичи:

- `src/repo_memory/lightrag_pilot.py` становится тонким facade module
- внутренняя логика разнесена по небольшим тематическим модулям
- public entrypoints и import compatibility сохраняются
- retrieval semantics и benchmark expectations не меняются
- дальнейшие targeted changes можно делать без возврата к 1300+ строкам в одном
  файле

## Users

- orchestrator, которому нужна безопасная граница следующего implementation PR
- implementation agent, которому нужна декомпозиция по модулям без скрытого
  behavior change
- review agent, которому нужен structural diff с чётким compatibility contract
- maintainer local `LightRAG` pilot-а, которому нужно легче сопровождать build,
  query и context-pack flow

## Scope

В scope входит:

- выделение констант и canonical policy data в отдельный модуль конфигурации
- выделение dataclass типов в отдельный модуль
- выделение Markdown chunking/preprocessing в отдельный модуль
- выделение query-policy and answer-shaping helpers в отдельный модуль
- выделение reference-resolution helpers в отдельный модуль
- выделение LightRAG runtime wiring в отдельный модуль
- выделение context-pack assembly в отдельный модуль
- сохранение `src/repo_memory/lightrag_pilot.py` как thin facade
- re-export нужных symbols там, где это требуется для обратной совместимости
- тесты, подтверждающие structural compatibility и отсутствие behavior drift

Target decomposition baseline:

- `src/repo_memory/pilot_config.py`
- `src/repo_memory/pilot_types.py`
- `src/repo_memory/markdown_chunks.py`
- `src/repo_memory/query_policy.py`
- `src/repo_memory/reference_resolution.py`
- `src/repo_memory/lightrag_runtime.py`
- `src/repo_memory/context_pack.py`
- `src/repo_memory/lightrag_pilot.py`

## Out Of Scope

Вне scope:

- изменения `working_dir`
- изменения corpus allowlist
- изменения default `QueryParam` semantics кроме механического переноса
- смена generation or embedding model
- `rerank` integration or enablement
- broad chunking-policy redesign
- extraction-quality redesign
- benchmark dataset changes
- новые retrieval heuristics beyond behavior-preserving extraction

## Non-Goals

Эта фича не должна:

- смешивать structural refactor с post-`048` quality tuning
- вводить новый public CLI contract
- ломать `src.repo_memory.lightrag_pilot:main`
- менять `scripts/lightrag_pilot.py` без явной необходимости
- трактовать internal module split как excuse для скрытого runtime behavior
  change

## Core Principles

### 1. Structure changes, behavior does not

Главный смысл фичи в улучшении module boundaries, а не в изменении retrieval
или indexing behavior.

### 2. Public compatibility stays stable

CLI entrypoint, script integration, and key public helpers should keep working
through the existing import path unless a separate future change explicitly
changes that contract.

### 3. Policy and heuristics stay separated

После refactor repository policy data, answer-shaping policy, reference
resolution, and runtime wiring должны жить в разных модулях, а не снова
схлопнуться в один "misc" слой.

### 4. Execution must stay attributable

Если после refactor поменяется benchmark behavior, это считается regression,
пока не доказано обратное.

## Functional Requirements

### FR1. Thin facade requirement

`src/repo_memory/lightrag_pilot.py` must become a thin facade responsible
primarily for:

- public `build_index`
- public `query_index`
- public `build_parser`
- public `main`
- compatibility re-exports where needed

### FR2. Internal concerns are split by responsibility

The existing mixed logic must be split into responsibility-focused modules
rather than arbitrary helper buckets.

### FR3. Import compatibility is preserved

Existing scripts and tests that import through
`src.repo_memory.lightrag_pilot` must continue to work unless the feature
explicitly records and validates a compatibility exception.

### FR4. Validation proves no behavior drift

The implementation loop must show that structural refactor does not degrade:

- build flow behavior
- query flow behavior
- context-pack assembly
- canonical answer shaping
- benchmark-relevant outputs within the existing acceptance scope

## Technical Requirements

### TR1. Must preserve official LightRAG lifecycle invariants

The refactor must keep the documented lifecycle around `LightRAG(...)`,
`initialize_storages()`, and `finalize_storages()` intact.

### TR2. Must preserve working-dir and runtime defaults

`working_dir`, Ollama wiring, and current runtime defaults must not change in
this feature except for mechanical relocation into dedicated modules.

### TR3. Must preserve corpus and policy boundaries

Corpus allowlist, mandatory-doc policy, and canonical document sets must remain
stable in this feature unless a separate future spec opens a policy change.

### TR4. Product-code changes require the implementation loop

All edits to `src/`, `tests/`, or runtime scripts must land through the
standard isolated worktree/branch/PR loop rather than the main checkout.

## Acceptance Criteria

### AC1. The facade is materially smaller

`src/repo_memory/lightrag_pilot.py` is reduced to a thin facade target of
roughly `< 300` lines, with the rest of the logic moved into dedicated modules.

### AC2. Module boundaries are explicit

A reader can identify where configuration, types, chunking, query policy,
reference resolution, runtime wiring, and context-pack assembly each live.

### AC3. Public behavior remains stable

Existing tests pass and no benchmark-result drift is introduced by the
structural refactor itself.

### AC4. Follow-up work becomes narrower

After the refactor, future retrieval-quality, extraction, or runtime changes can
target isolated modules instead of re-entering a monolith.

## Validation

Minimum validation for this feature:

1. Freeze the target module split and public compatibility constraints.
2. Execute the refactor through an isolated implementation worktree/PR loop.
3. Run the current automated tests that cover `lightrag_pilot` behavior.
4. Confirm that the facade remains the public entrypoint.
5. Confirm that benchmark expectations do not change as a side effect.

## References

- `specs/042-repo-memory-platform-lightrag/spec.md`
- `specs/047-track-b-corpus-expansion/evaluation.md`
- `specs/048-post-047-retrieval-quality-tuning/evaluation.md`
- `docs/context-policy.md`
- `docs/lightrag-local-pilot.md`
