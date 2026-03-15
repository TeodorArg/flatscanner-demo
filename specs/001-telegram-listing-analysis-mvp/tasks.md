# Tasks: Telegram Listing Analysis MVP

## Spec

- [x] Define the first end-to-end user flow through Telegram
- [x] Capture the platform-agnostic adapter requirement for future listing providers
- [x] Record the MVP output expectations for summary, risks, and price fairness

## Documentation

- [x] Update durable product context for the universal listing-analysis direction
- [x] Record the initial backend architecture in an ADR
- [x] Update backend docs with the chosen stack and design constraints

## Implementation

- [x] Scaffold the Python backend structure under `src/`
- [x] Add FastAPI application bootstrap and configuration handling
  - [x] Add Python CI step (install + pytest) to enforce the new tests in CI
  - [x] Fix `create_app()` to instantiate fresh `Settings()` on each call instead of relying on the cached `get_settings()`
- [x] Add Telegram bot entrypoints and message routing
- [ ] Define normalized listing schemas and persistence models
- [ ] Add provider detection and the Airbnb adapter interface
- [ ] Integrate Apify-backed Airbnb extraction
- [ ] Add background job orchestration using Redis
- [ ] Add initial AI analysis flow through OpenRouter
- [ ] Format Telegram output for summary, risks, and price fairness

## Validation

- [ ] Add tests for provider detection
- [ ] Add tests for normalized listing mapping
- [ ] Add tests for Telegram output formatting
- [ ] Add orchestration tests for partial enrichment scenarios

## Follow-Up

- [ ] Decide the first enrichment provider set for safety, transport, and nearby places
- [ ] Decide the long-term worker library choice on top of Redis
- [ ] Define how price fairness will use comparables versus heuristic signals
