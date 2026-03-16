# Feature Spec: AI Pull Request Workflow

## Status

Completed

## Goal

Define the default repository delivery model for AI-assisted implementation, review, and merge.

## Resolution

- Claude is the product-code implementation agent.
- Codex owns architecture, CI/CD, and review policy.
- Product changes land through pull requests.
- `AI Review` is a required self-hosted check alongside `baseline-checks` and `guard`.
- Human approval remains the final merge gate.

## Follow-Up

- Decide later whether Claude PR creation should also start from issues or slash commands.
