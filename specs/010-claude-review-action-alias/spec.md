# Feature Spec: Claude Review Action Alias Support

## Status

Completed

## Goal

Keep `AI Review` stable when Claude returns another observed compatible status field instead of `verdict`.

## Resolution

- `review_action` is normalized to `verdict` when the value is valid.
- Local regression coverage now includes `action`, `review_status`, and `review_action`.
