# Technical Plan: Simplified Airbnb Review Source

## Approach

Introduce a small review-source seam inside
`src/analysis/reviews/airbnb_source.py` and keep the module surface stable.

## Planned Changes

### 1. Settings

Add:

- `apify_airbnb_reviews_actor_id`

### 2. Source abstraction

Refactor `AirbnbReviewSource` so it returns `ReviewExtractionResult` directly
for the configured actor.

### 3. Reviews module

Keep `AirbnbReviewsModule` source-agnostic:

- ask the source for an extraction result
- fall back to `ctx.raw_payload`
- then generic metadata fallback

### 4. Runtime wiring

Construct the source from settings in the job processor.

### 5. Tests

Add/update tests for:

- default actor selection
- input payload shape for the listing-payload actor
- actor override behavior
- module fallback behavior

## Risks

- The curious_coder actor may return fewer reviews than other actors for some
  listings. This is acceptable for the cost-reduction rollback slice.

## Validation

- targeted pytest for review source + review module + processor
- live smoke on VPS confirming reviews still render
