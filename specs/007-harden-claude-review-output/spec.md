# Feature Spec: Harden Claude Review Output Parsing

## Context

The repository uses Claude Code CLI as one of the supported AI review backends. In a live PR review run, Claude returned JSON that used `action` instead of `verdict`, which caused the wrapper script to fail before posting the sticky AI review comment. That turned a reviewable PR into a red workflow with weak diagnostics.

## Scope

- Make the Claude review adapter tolerant of compatible JSON field variants
- Improve diagnostics so raw Claude output is inspectable when parsing or validation fails
- Add repository-local validation coverage for Claude review output parsing
- Update durable workflow docs to describe the stronger diagnostics path

## Out Of Scope

- Changing the Codex review adapter contract
- Changing the selected AI reviewer policy
- Product application code changes

## Requirements

- The Claude review adapter must accept `action` as a compatible synonym for `verdict` when the value is one of `approve`, `comment`, or `request_changes`
- The Claude review adapter must persist raw model output to a durable temp log before schema validation
- The AI review workflow must print the Claude raw-output log in GitHub job logs when present
- Claude review parsing must keep rejecting truly invalid or missing review payloads
- Repository-local validation must cover both `verdict` and `action` response shapes

## Acceptance Criteria

- A Claude response with `action` but no `verdict` still produces a valid sticky AI review comment
- Raw Claude output is available in workflow logs when parsing fails
- Local validation covers compatible field normalization and invalid payload handling
- Durable docs explain that AI review logs now include raw Claude output for debugging
