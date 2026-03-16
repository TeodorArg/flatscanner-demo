# Feature Spec: Claude Review Status Alias Support

## Context

After the Claude review parser was hardened for `action`-style payloads, a live PR review still failed because Claude returned `review_status` instead of `verdict`. The repository needs the Claude adapter to tolerate this compatible status alias as well so `AI Review` reflects real review content instead of parser churn.

## Scope

- Normalize `review_status` to `verdict` in the Claude review parser when the value is compatible
- Add regression coverage for the observed `review_status` payload shape
- Update operator docs so supported Claude status aliases are explicit

## Requirements

- The Claude review parser must accept `review_status` as a compatible synonym for `verdict`
- Only `approve`, `comment`, and `request_changes` remain valid normalized verdict values
- Repository-local validation must cover the observed `review_status` payload shape

## Acceptance Criteria

- A Claude response with `review_status` and no `verdict` produces a valid parsed review result
- Local validation covers `verdict`, `action`, and `review_status`
