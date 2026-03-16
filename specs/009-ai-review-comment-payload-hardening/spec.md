# Feature Spec: AI Review Comment Payload Hardening

## Status

Completed

## Goal

Prevent `AI Review` from failing when the review result is valid but the sticky GitHub comment body contains problematic characters or grows too large.

## Resolution

- Review comments are sanitized before posting.
- Comment bodies are posted as explicit JSON with UTF-8 content type.
- Oversized review comments are truncated to stay within GitHub issue-comment limits.
- Repository-local validation covers payload sanitization and truncation behavior.
