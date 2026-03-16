# Feature Spec: Neutral AI Runner Label

## Status

Completed

## Goal

Rename the self-hosted review runner label to an agent-neutral name.

## Resolution

- Repository workflows target `ai-runner`.
- Setup and migration helpers default to `ai-runner`.
- The migration helper keeps legacy `codex` unless an operator explicitly removes it.
