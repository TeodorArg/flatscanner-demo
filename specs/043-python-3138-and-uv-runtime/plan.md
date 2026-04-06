# Plan: Python 3.13.8 And `uv` Runtime

## Summary

Standardize the repository on `Python 3.13.8` for local project work and on
`uv` as the canonical environment and dependency workflow.

The first pass focuses on repository-facing runtime files and canonical setup
instructions, not on unrelated product-code behavior.

## Files And Areas

- `.python-version`
- `pyproject.toml`
- `Dockerfile`
- `.github/workflows/ci.yml`
- `README.md`
- `specs/043-python-3138-and-uv-runtime/`

## Risks

- narrowing Python expectations too aggressively could conflict with later CI
  or deployment assumptions
- partial migration to `uv` would increase runtime confusion rather than reduce
  it
- Docker and runtime instructions may drift if local and CI paths are not
  updated together

## Validation

- confirm `.python-version` resolves to `3.13.8`
- create a repo-local environment with `uv`
- verify project installation through `uv`
- verify CI workflow uses `uv`
- verify README setup note matches the implemented commands

## Notes

- This feature is about repository runtime consistency, not product behavior.
- The runtime baseline is `Python 3.13.8`.
