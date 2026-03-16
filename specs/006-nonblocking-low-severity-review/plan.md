# Implementation Plan: Non-Blocking Low-Severity AI Review Findings

## Summary

Add shared verdict normalization so low-severity-only findings downgrade to advisory comments while medium and high findings can still block merge.

## Touched Areas

- reviewer prompts
- shared review-policy script
- Claude and Codex review adapters
- workflow docs and ADR 002

## Validation Completed

- PowerShell parser checks
- local verdict-normalization validation
- sticky comment still reports the effective verdict cleanly
