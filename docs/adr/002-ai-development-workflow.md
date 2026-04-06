# ADR 002: AI Development Workflow

## Status

Accepted

## Context

The repository needed an explicit delivery model for spec-driven implementation, automated review, and human-controlled merge.

## Decision

- Claude is the primary implementation agent for product code.
- Codex owns architecture, CI/CD, and review policy.
- Product code lands through pull requests, not direct pushes to `main`.
- Durable docs, specs, prompts, ADRs, and workflow files may be edited directly by Codex.
- Every PR must pass `baseline-checks`, `guard`, and `AI Review`.
- Automated review runs on a self-hosted runner labeled `ai-runner`.
- Runner strategy is selected through `AI_REVIEW_RUNNER`, with supported
  values `windows` and `macOS` and fallback `windows`.
- The active reviewer is selected only through `AI_REVIEW_AGENT`, with supported values `claude` and `codex` and fallback `claude`.
- Low-severity-only findings stay advisory and must not fail `AI Review`.

## Consequences

- Roles and merge gates are explicit.
- Review infrastructure becomes part of the repository architecture.
- Human approval remains the final merge gate even with automated AI review.
