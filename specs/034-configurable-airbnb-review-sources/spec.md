# Feature Spec: Simplified Airbnb Review Source

## Goal

Reduce review-scraping cost and keep Airbnb review ingestion easy to override
without rewriting module logic.

## Problem

The review path had become more expensive than necessary because it depended on
an actor that billed per extracted review item.

The runtime design had also grown more complex than needed for the current
product path.

## Scope

In scope:

- simplified Airbnb review actor configuration
- default rollback to `curious_coder` for reviews
- stable module contract independent of source-specific payload shape
- minimal config changes to switch review actors later

Out of scope:

- review corpus caching
- review sampling / max review caps
- changes to listing price actor
- new Web UI behavior

## Requirements

### R1. Single review source abstraction

The Airbnb reviews module must fetch through a single source abstraction rather
than embedding actor logic in the module itself.

### R2. Default to lower-cost reviews path

The default review source should use the legacy
`curious_coder/airbnb-scraper` listing payload path for reviews.

### R3. Preserve easy actor override

Switching to another compatible Airbnb review actor must remain possible
through configuration only.

### R4. Module stays source-agnostic

`AirbnbReviewsModule` should consume a unified extraction result instead of
knowing whether reviews came from:

- a listing payload actor
- another compatible review source
- the embedded raw payload fallback

## Acceptance Criteria

- A review source abstraction exists for Airbnb reviews.
- Default runtime configuration uses the curious_coder listing payload path.
- Switching actors can be done through `APIFY_AIRBNB_REVIEWS_ACTOR_ID`.
- Tests cover the default actor path, actor override, and module fallback behavior.
