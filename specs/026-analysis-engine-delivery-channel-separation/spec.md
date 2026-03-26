# Feature Spec: Analysis Engine / Delivery Channel Separation

## Context

The current application still treats Telegram as the primary runtime boundary:
the router enqueues Telegram-shaped jobs, the worker updates Telegram progress
messages directly, and the final result is formatted and delivered only as a
Telegram message.

That was acceptable for the bot-first MVP, but the next product step adds a
Web UI that must submit analysis requests, observe progress, and fetch results
from the same backend engine. Without an explicit separation between the
analysis platform and delivery channels, every new client would force more
channel-specific conditionals into the core pipeline.

## Goal

Refactor the backend so that:

1. The analysis engine is channel-agnostic.
2. Telegram becomes one delivery channel implementation.
3. A future Web UI can use the same submission, progress, and result pipeline.
4. Channel-specific progress and presentation live behind explicit interfaces.

## Scope

- Introduce explicit delivery-channel abstractions in the application layer.
- Remove Telegram-specific assumptions from the core job execution contract.
- Define channel-specific progress and result-delivery interfaces.
- Preserve the current Telegram UX and behavior during the migration.
- Break the refactor into small implementation slices that can land safely.

## Out Of Scope

- Building the Web UI itself.
- Shipping browser auth, sessions, or frontend styling.
- Replacing Redis or the current worker loop.
- Reworking billing, cache, or settings in this feature.

## Current Problem Areas

- `AnalysisJob` still carries Telegram-specific fields.
- `process_job` sends Telegram progress updates directly.
- Final result delivery is embedded in the worker pipeline.
- There is no shared submission/use-case layer for multiple clients.

## Target Architecture

### Core Analysis Platform

The core platform owns:

- request submission
- queue orchestration
- adapter fetch + raw payload capture
- enrichment
- analysis modules
- translation
- result assembly

The platform must not depend on Telegram message schemas or Telegram sender
functions directly.

### Delivery Channels

Delivery channels are pluggable adapters that sit on top of the core platform:

- Telegram
- future Web UI
- future API consumers

Each channel is responsible for:

- intake mapping
- progress reporting
- channel-specific presentation
- channel-specific delivery metadata

### Channel-Neutral Job Shape

The core job model must represent:

- source URL
- provider
- language
- delivery channel
- channel context reference / payload

Telegram-specific fields must move out of the core job shape and into a
channel-specific delivery context.

### Progress Reporting

The engine reports progress through a channel-neutral interface, for example:

- `start()`
- `update(stage)`
- `complete()`
- `fail()`

Telegram implements this as:

- initial progress message
- edited stage updates
- typing heartbeat
- delete progress message before final result

Web will later implement it as:

- persisted stage state
- polling / SSE / websocket updates

### Result Presentation

The engine produces structured analysis results.

Presentation must be delegated to channel-specific presenters:

- `TelegramPresenter`
- future `WebResultPresenter` / serializer

The worker should not hard-code Telegram formatting as the only output path.

## Migration Slices

| Slice | Name | Scope |
|---|---|---|
| S1 | Delivery foundation | Delivery channel enum, channel context models, progress sink abstraction |
| S2 | Submission/use-case layer | Shared `submit_analysis_request` + `run_analysis_job` application services |
| S3 | Telegram presenter split | Move Telegram formatting/delivery behind a presenter implementation |
| S4 | Web delivery foundation | Add web-friendly result/progress read models and API endpoints |
| S5 | Web UI integration | Connect frontend client to submission/progress/result APIs |

## Acceptance Criteria

- This feature has a spec, plan, and task breakdown.
- The migration path is explicit and incremental.
- Telegram behavior remains stable while the abstractions are introduced.
- Follow-up implementation slices can land one by one without a big-bang rewrite.
