# Implementation Plan: Analysis Engine / Delivery Channel Separation

## Strategy

Use a strangler migration:

1. Introduce delivery abstractions next to the current Telegram path.
2. Move the worker pipeline to depend on abstractions instead of Telegram
   helpers directly.
3. Keep Telegram as the first concrete implementation.
4. Only after the abstraction is stable, add the Web delivery path.

## First Safe Slice

### Slice S1: Delivery Foundation

Introduce the smallest runtime seam that unlocks future separation:

- `DeliveryChannel` enum
- channel-specific context models (`TelegramDeliveryContext`, future `WebDeliveryContext`)
- `ProgressSink` protocol / interface
- `TelegramProgressSink` as the first implementation
- worker pipeline updated to depend on `ProgressSink` rather than direct
  Telegram progress helper calls

This slice does **not** yet remove Telegram final-result delivery from the
worker; it only removes Telegram-specific progress handling from the engine.

## Touched Areas

- `src/domain/`
- `src/jobs/`
- `src/telegram/`
- `tests/`
- `docs/project/backend/backend-docs.md` if durable wording needs updating

## Risks

- Telegram progress UX can regress if stage updates or cleanup move incorrectly.
- Job shape changes can break queue serialization/deserialization.
- Over-scoping the first slice would slow the refactor and increase risk.

## Validation

- existing test suite remains green
- focused tests for channel context serialization and `ProgressSink` behavior
- integration tests prove Telegram progress UX still works through the new abstraction
