# Implementation Plan: Claude Review Status Alias Support

## Summary

Extend the Claude review output parser to normalize another observed status alias, `review_status`, into the shared `verdict` field. This keeps the hardening fix aligned with live Claude output without weakening the review contract.

## Files And Areas

- `scripts/claude-review-output.ps1` for alias normalization
- `scripts/test-claude-review-output-parsing.ps1` for regression coverage
- `docs/project/backend/self-hosted-runner.md` for operator-facing note about compatible status aliases
- `specs/008-claude-review-status-alias/` for execution tracking

## Validation

- Parse the updated PowerShell scripts successfully
- Run the Claude review output parsing validation script successfully
- Confirm the observed `review_status` payload shape normalizes to a valid verdict
