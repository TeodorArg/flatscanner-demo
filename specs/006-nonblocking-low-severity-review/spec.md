# Feature Spec: Non-Blocking Low-Severity AI Review Findings

## Status

Completed

## Goal

Keep minor AI review findings advisory so the required review check blocks only on meaningful issues.

## Resolution

- Low-severity-only findings are non-blocking.
- `AI Review` fails only when the effective verdict remains `request_changes`.
- The sticky review comment shows the normalized effective verdict.
