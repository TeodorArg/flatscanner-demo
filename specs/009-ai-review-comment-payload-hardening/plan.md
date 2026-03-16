# Implementation Plan: AI Review Comment Payload Hardening

## Summary

Add a shared comment-payload helper for Claude and Codex review adapters so GitHub issue-comment writes stay reliable even when model output includes unusual characters or long findings.

## Touched Areas

- `scripts/run-claude-pr-review.ps1`
- `scripts/run-codex-pr-review.ps1`
- shared comment payload helper and validation script
- CI validation step
- runner operations docs

## Validation Completed

- local payload validation
- local Claude parser validation
- live `AI Review` success on the hardening PR
