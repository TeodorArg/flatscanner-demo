# Implementation Plan: Claude Review Status Alias Support

## Summary

Extend the shared Claude parser so observed `review_status` payloads normalize cleanly into the existing verdict contract.

## Touched Areas

- `scripts/claude-review-output.ps1`
- parser regression tests
- runner docs

## Validation Completed

- PowerShell parser checks
- local parsing validation for `review_status`
