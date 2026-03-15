# Tasks: Switchable AI Reviewer

## Spec

- [x] Define the repository-variable-only reviewer selection rule
- [x] Define the supported reviewer values and `claude` fallback behavior
- [x] Keep one stable `AI Review` required check

## Documentation

- [x] Update durable workflow docs for switchable AI review
- [x] Update runner setup docs for `AI_REVIEW_AGENT`
- [x] Update agent instructions and Claude playbooks for the neutral `AI Review` path
- [x] Record the durable workflow change in ADR 002

## Workflow And Scripts

- [x] Add a shared AI review selector script
- [x] Add a Claude review adapter script
- [x] Update the Codex review adapter to the neutral AI review contract
- [x] Update the AI review workflow to select the reviewer from `AI_REVIEW_AGENT`
- [x] Update Claude fix automation to consume the shared sticky AI review comment
- [x] Add a Claude-specific PR review prompt
- [x] Move the review schema to a shared location

## Validation

- [x] Parse the updated PowerShell scripts successfully
- [x] Validate reviewer selection for `claude`
- [x] Validate reviewer selection for `codex`
- [x] Validate fallback reviewer selection for invalid or missing values
- [x] Add lightweight repository-local validation scripts for reviewer selection and Claude no-tools CLI smoke testing

## Follow-Up

- [ ] Decide whether to rename the self-hosted runner label from `codex` to a neutral label later
- [ ] Decide whether to add an optional shadow reviewer mode in a future workflow iteration
