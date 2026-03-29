# Technical Plan: Remove Dedicated Airbnb Review Actor

## Approach

Keep the existing `AirbnbReviewSource` seam, but simplify it to one
listing-payload actor path with an optional actor-id override.

## Planned Changes

1. Simplify `src/analysis/reviews/airbnb_source.py`
2. Remove strategy-specific settings from `src/app/config.py`
3. Update `src/jobs/processor.py` runtime wiring
4. Simplify `tests/test_airbnb_review_source.py`
5. Scrub docs and specs of the removed actor references
6. Verify local search and VPS runtime are clean
