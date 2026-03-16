# Implementation Plan: Harden Claude Review Output Parsing

## Summary

Add tolerant Claude parsing, durable raw-output logging, and local regression coverage so parser drift no longer breaks `AI Review`.

## Touched Areas

- `scripts/run-claude-pr-review.ps1`
- shared Claude parsing helpers and tests
- `ai-review.yml`
- runner and workflow docs

## Validation Completed

- PowerShell parser checks
- local parser validation
- workflow log visibility for raw Claude output
