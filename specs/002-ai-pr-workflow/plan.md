# Implementation Plan: AI Pull Request Workflow

## Summary

Make pull requests the only merge path by wiring agent contracts, self-hosted AI review, fix automation, and durable workflow docs.

## Touched Areas

- `AGENTS.md`, `CLAUDE.md`
- `.github/workflows/ai-review.yml`, `.github/workflows/claude-fix-pr.yml`
- review prompts, schema, and orchestration scripts
- `docs/ai-pr-workflow.md`, `docs/project/backend/self-hosted-runner.md`, `docs/adr/002-ai-development-workflow.md`

## Validation Completed

- self-hosted runner registered and branch protection enabled
- live PR loop verified for sticky review comments and follow-up fixes
- false-negative review exits hardened with durable diagnostics
