# Spec: Python 3.13.8 And `uv` Runtime

## Feature ID

- `043-python-3138-and-uv-runtime`

## Context

The repository currently has inconsistent local-runtime signals:

- the active local baseline in the main checkout is `Python 3.13.8`
- `pyproject.toml` currently allows a different Python range
- some canonical setup paths still use `pip`

This creates avoidable drift for local setup, CI behavior, and reproducible
runtime validation.

The repository needs one explicit local Python baseline and one explicit
project package/environment workflow.

## Scope

This feature defines and rolls out the repository runtime baseline:

- pin the local project Python version to `3.13.8`
- adopt `uv` as the required project environment and package workflow
- replace canonical `pip`-based project setup paths with `uv` where the
  repository defines them as current practice
- align docs and runtime-facing project files with the chosen baseline

## Out Of Scope

- changing the production application architecture
- refactoring unrelated product code
- changing the `LightRAG` ingestion or retrieval design itself

## Requirements

- The repository must expose one explicit local Python baseline via
  `.python-version`.
- The chosen baseline for this feature is `Python 3.13.8`.
- Canonical project setup and dependency-installation instructions must use
  `uv`.
- Repository runtime files must stop implying a Python baseline different from
  `3.13.8`.
- Canonical project files that install project dependencies must use one
  consistent package workflow unless a file is explicitly historical.

## Acceptance Criteria

- `.python-version` is pinned to `3.13.8`.
- Canonical project runtime/setup files are aligned with `Python 3.13.8`.
- Canonical project environment/setup instructions use `uv`.
- CI installs project dependencies through `uv`.
- Feature memory lists the exact files changed for this baseline decision.

## Open Questions

- Whether `pyproject.toml` should stay `>=3.13,<3.14` long term or be widened
  later once the rest of the toolchain is revalidated.
