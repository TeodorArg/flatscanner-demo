# Feature Spec: Harden Claude Review Output Parsing

## Status

Completed

## Goal

Keep Claude review failures from being caused by compatible output-shape drift instead of actual review content.

## Resolution

- Claude review parsing accepts compatible `action` as a `verdict` alias.
- Raw model output is saved and printed in workflow diagnostics.
- Local validation covers normalized and invalid payload shapes.
