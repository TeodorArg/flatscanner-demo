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
  - [x] Add webhook secret-token authentication (PR-5-fix-2)
  - [x] Raise on non-2xx Telegram API responses in send_message (PR-5-fix-2)
  - [x] Require telegram_webhook_secret outside development/testing environments (PR-5-fix-3)
  - [x] Fix stale HTML parse mode claim in sender.py docstring (PR-5-fix-3)
  - [x] Require telegram_bot_token outside development/testing environments (PR-5-fix-4)
  - [x] Return 502 on send_message failure so Telegram retries the update (PR-5-fix-5)
  - [x] Gate routing on supported providers; unsupported URLs get explicit non-analysis reply (PR-5-fix-6)
  - [x] Recognise abnb.me short/share links as supported Airbnb URLs (PR-5-fix-7)
  - [x] Inspect all URLs in a message and choose a supported listing URL when present (PR-5-fix-8)
  - [x] Tighten provider detection to airbnb.com/rooms/<id> listing paths only; abnb.me share links remain supported (PR-5-fix-8)
  - [x] Move webhook secret validation ahead of request body parsing so unauthenticated requests are rejected before schema validation (PR-5-fix-8)
  - [x] Expand Airbnb provider detection to cover all localized domains (e.g. airbnb.co.uk, airbnb.de, airbnb.com.au) while keeping listing-path restriction (PR-5-fix-9)
  - [x] Acknowledge permanent 4xx Telegram delivery failures (return 200); return 502 only for transient 5xx/network errors so Telegram retries appropriately (PR-5-fix-9)
  - [x] Treat 429 Too Many Requests as transient (return 502 so Telegram retries); other 4xx remain permanent (PR-5-fix-11)
  - [x] Require a real listing ID after /rooms/ (bare /rooms/ path rejected); require non-empty path for abnb.me shortlinks (PR-5-fix-10)
  - [x] Route messages with Airbnb URLs in media captions the same as text messages (PR-5-fix-10)
  - [x] Anchor /rooms/<id> path matcher to reject extra segments like /rooms/123/photos (PR-5-fix-12)
  - [x] Replace broad localized-Airbnb regex with explicit supported-domain TLD allowlist; reject non-http/https schemes inside is_supported_provider() (PR-5-fix-13)
- [x] Define normalized listing schemas and persistence models
- [ ] Add provider detection and the Airbnb adapter interface
- [ ] Integrate Apify-backed Airbnb extraction
- [ ] Add background job orchestration using Redis
- [ ] Add initial AI analysis flow through OpenRouter
- [ ] Format Telegram output for summary, risks, and price fairness

## Validation

- [x] Add tests for provider detection (URL routing and is_supported_provider — PR-5-fix-8)
- [x] Add tests for localized Airbnb domain detection (PR-5-fix-9)
- [x] Add tests for 4xx-vs-5xx webhook failure differentiation (PR-5-fix-9)
- [x] Add tests for malformed /rooms/ and abnb.me URLs, and caption-based routing (PR-5-fix-10)
- [x] Add test for 429 Too Many Requests treated as transient retry (PR-5-fix-11)
- [x] Add regression test that /rooms/123/photos extra-segment URLs are rejected (PR-5-fix-12)
- [x] Add negative tests for bogus ccTLD hosts and non-web schemes (PR-5-fix-13)
- [x] Add tests for normalized listing mapping
- [ ] Add tests for Telegram output formatting
- [ ] Add orchestration tests for partial enrichment scenarios

## Follow-Up

- [ ] Decide the first enrichment provider set for safety, transport, and nearby places
- [ ] Decide the long-term worker library choice on top of Redis
- [ ] Define how price fairness will use comparables versus heuristic signals
