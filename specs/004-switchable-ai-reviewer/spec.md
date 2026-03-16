# Feature Spec: Switchable AI Reviewer

## Status

Completed

## Goal

Allow either Claude or Codex to run PR review without changing the surrounding merge contract.

## Resolution

- Reviewer selection comes only from `AI_REVIEW_AGENT`.
- Supported reviewers are `claude` and `codex`; fallback is `claude`.
- The required check stays `AI Review`.
- Both adapters publish the same sticky comment contract.

## Follow-Up

- Decide later whether to add an optional shadow reviewer mode.
