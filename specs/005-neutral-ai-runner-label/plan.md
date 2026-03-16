# Implementation Plan: Neutral AI Runner Label

## Summary

Switch self-hosted workflow targeting from `codex` to `ai-runner`, update setup defaults, and add a repository-local migration helper.

## Touched Areas

- self-hosted workflow `runs-on` labels
- runner setup and migration scripts
- backend and workflow docs
- ADR alignment

## Validation Completed

- PowerShell parser checks
- workflow YAML validation
- live GitHub confirmation that the runner exposes `ai-runner`
