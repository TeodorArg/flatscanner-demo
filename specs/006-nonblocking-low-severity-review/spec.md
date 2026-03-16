# Feature Spec: Non-Blocking Low-Severity AI Review Findings

## Context

The repository now relies on automated AI review as a required check. In live PR runs, the reviewer can occasionally emit `request_changes` for findings that are operationally minor or clearly low severity. That creates avoidable merge friction because `AI Review` fails even when the PR only needs advisory follow-up.

## Scope

- Define the repository policy for how low-severity AI review findings affect merge blocking
- Normalize reviewer output so low-severity-only findings never fail the required `AI Review` check
- Keep the sticky AI review comment transparent about the effective verdict after policy normalization
- Update durable docs, ADR guidance, and review prompts to match the policy

## Out Of Scope

- Introducing a shadow reviewer mode
- Changing the supported AI reviewers
- Product application code changes

## Requirements

- Low-severity-only AI review findings must remain advisory and must not fail the `AI Review` check
- `AI Review` may fail only when the effective verdict remains `request_changes`
- If a reviewer emits `request_changes` with only low-severity findings or with no findings, the workflow must normalize the effective verdict to `comment`
- The sticky AI review comment must clearly show the effective verdict seen by GitHub reviewers
- Review prompts and durable docs must describe low-severity findings as non-blocking

## Acceptance Criteria

- Both Codex and Claude review adapters apply the same low-severity normalization policy
- The normalization behavior is covered by a repository-local validation script
- Durable docs and ADR 002 describe low-severity findings as advisory
- The open follow-up in `specs/002-ai-pr-workflow/tasks.md` is resolved in favor of non-blocking low-severity findings

## Resolution

- Low-severity AI review findings remain non-blocking advisory comments unless a future feature explicitly changes the policy
