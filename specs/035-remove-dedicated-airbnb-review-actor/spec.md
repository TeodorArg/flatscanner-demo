# Feature Spec: Remove Dedicated Airbnb Review Actor

## Goal

Remove the legacy dedicated Airbnb reviews actor from code, configuration, and
repository memory so the project uses one low-cost review path by default.

## Scope

In scope:

- remove legacy dedicated review-actor support from runtime code
- simplify review configuration to one actor override
- scrub remaining references from docs and feature memory
- verify the server runtime only uses the listing-payload review actor

Out of scope:

- review caching
- new review providers
- changes to the Airbnb listing actor

## Acceptance Criteria

- runtime code no longer supports the removed dedicated Airbnb reviews actor
- repository search finds no remaining references to the removed actor path
- VPS runtime configuration uses only the listing-payload review actor
