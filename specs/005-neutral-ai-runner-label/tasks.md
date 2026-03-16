# Tasks: Neutral AI Runner Label

## Spec

- [x] Define the neutral self-hosted runner label scope
- [x] Keep the self-hosted runner architecture while renaming the label to `ai-runner`
- [x] Record the required live migration constraint before workflow cutover

## Documentation

- [x] Update durable backend and workflow docs for `ai-runner`
- [x] Update ADRs that still describe `codex` as the required runner label
- [x] Record the resolved follow-up in `specs/004-switchable-ai-reviewer/tasks.md`

## Workflow And Scripts

- [x] Update GitHub workflow `runs-on` labels to `ai-runner`
- [x] Update self-hosted runner setup defaults to `ai-runner`
- [x] Add a repository-local helper for applying the `ai-runner` label to an existing GitHub runner

## Validation

- [x] Parse the updated PowerShell scripts successfully
- [x] Validate workflow YAML after the runner-label change
- [x] Confirm GitHub shows the current runner with the `ai-runner` label

## Follow-Up

- [x] Keep the legacy `codex` runner label by default until an operator explicitly removes it
