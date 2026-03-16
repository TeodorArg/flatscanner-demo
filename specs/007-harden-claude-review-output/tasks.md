# Tasks: Harden Claude Review Output Parsing

## Spec

- [x] Define the Claude review parsing hardening scope
- [x] Record the need for compatible `action` to `verdict` normalization
- [x] Require stronger raw-output diagnostics for Claude review failures

## Documentation

- [x] Update durable workflow docs for Claude raw-output diagnostics
- [x] Record the stronger diagnostics path for self-hosted review operators

## Workflow And Scripts

- [x] Add shared Claude review output parsing helpers
- [x] Update the Claude review adapter to normalize compatible `action` payloads
- [x] Persist raw Claude output before schema validation
- [x] Update the AI review workflow to print the raw Claude output log
- [x] Add repository-local validation for Claude review output parsing

## Validation

- [x] Parse the updated PowerShell scripts successfully
- [x] Run the Claude review output parsing validation script successfully
- [x] Confirm the workflow logs can surface Claude raw output for debugging
