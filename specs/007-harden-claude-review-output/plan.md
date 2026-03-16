# Implementation Plan: Harden Claude Review Output Parsing

## Summary

Fix the Claude review wrapper so compatible model output does not fail the required `AI Review` check for parser reasons alone. Add tolerant parsing for `action`-style payloads, save raw Claude output to a temp log, and extend local validation so this regression stays covered.

## Files And Areas

- `scripts/run-claude-pr-review.ps1` for tolerant parsing and diagnostics
- `scripts/` for shared Claude review output parsing helpers and validation scripts
- `.github/workflows/ai-review.yml` for printing the raw Claude output log
- `docs/ai-pr-workflow.md` and `docs/project/backend/self-hosted-runner.md` for operator-facing diagnostics guidance
- `specs/007-harden-claude-review-output/` for execution tracking

## Proposed Workflow

1. Claude review writes raw model output to a temp log immediately after CLI completion
2. A shared parser normalizes fenced JSON, extracts the JSON body, and maps `action` to `verdict` when compatible
3. The adapter validates the normalized result and posts the sticky AI review comment as usual
4. If parsing still fails, GitHub logs now include the raw Claude output log alongside diagnostics and transcript output

## Risks

- Overly permissive normalization could hide genuinely malformed review output
- Diagnostics can become noisy if raw output logging is not truncated or clearly separated
- Validation can drift if parser logic and local tests are updated independently

## Validation

- Parse the updated PowerShell scripts successfully
- Run repository-local validation for Claude review output parsing
- Confirm the workflow prints the raw Claude output log when present
