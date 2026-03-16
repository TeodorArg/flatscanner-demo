# Tasks: Non-Blocking Low-Severity AI Review Findings

## Spec

- [x] Define the low-severity non-blocking AI review policy
- [x] Keep one required `AI Review` check while normalizing advisory findings
- [x] Record the durable policy resolution for low-severity findings

## Documentation

- [x] Update durable workflow docs for advisory low-severity findings
- [x] Update ADR 002 with the low-severity non-blocking policy
- [x] Resolve the open follow-up in `specs/002-ai-pr-workflow/tasks.md`

## Workflow And Scripts

- [x] Add shared low-severity verdict normalization for AI review adapters
- [x] Update Codex review adapter to use the effective verdict
- [x] Update Claude review adapter to use the effective verdict
- [x] Update reviewer prompts so low-severity findings use advisory comments
- [x] Add a repository-local validation script for verdict normalization

## Validation

- [x] Parse the updated PowerShell scripts successfully
- [x] Run the local verdict normalization validation script successfully
- [x] Confirm the sticky review comment still shows the effective verdict cleanly
