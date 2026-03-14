# Tasks: Local Claude Worker Orchestration

## Spec

- [x] Define the local Claude worker orchestration scope
- [x] Define worktree isolation and branch ownership rules
- [x] Keep the existing PR review loop as the only merge path

## Documentation

- [x] Add a durable ADR for local Claude worker orchestration
- [x] Add a durable operator guide for launching Claude workers
- [x] Update workflow docs to integrate local worker launches with the PR pipeline
- [x] Update agent instructions with worktree isolation rules

## Scripts

- [x] Add a script to create isolated Claude worker worktrees
- [x] Add a script to launch Claude CLI for one scoped task
- [x] Add a script to publish or reuse a pull request from a worker branch
- [x] Add a reusable Claude worker prompt template

## Validation

- [x] Parse the new PowerShell scripts successfully
- [x] Validate temporary worktree creation through the new script
- [x] Validate worker prompt generation with `-PromptOnly`
- [x] Validate publish script dry-run behavior with `-WhatIf`

## Follow-Up

- [ ] Decide whether to automate worker queueing and concurrency caps beyond operator discipline
- [ ] Decide whether PR creation should later move into a dedicated workflow trigger
