# Implementation Plan: Switchable AI Reviewer

## Summary

Add a shared selector that reads `AI_REVIEW_AGENT`, dispatches to the Claude or Codex adapter, and preserves one stable `AI Review` status check and sticky comment contract.

## Touched Areas

- `ai-review.yml` and review scripts
- shared schema and reviewer prompts
- workflow and runner docs
- ADR 002

## Validation Completed

- workflow YAML and PowerShell parser checks
- selector validation for `claude`, `codex`, invalid, and missing values
- branch-protection alignment with the stable `AI Review` check
