# Implementation Plan: Claude Review Action Alias Support

## Summary

Extend the shared Claude parser to normalize the observed `review_action` field into the existing `verdict` contract.

## Touched Areas

- `scripts/claude-review-output.ps1`
- parser regression validation
- runner operator docs

## Validation Completed

- local parser validation for `review_action`
- durable operator note updated
