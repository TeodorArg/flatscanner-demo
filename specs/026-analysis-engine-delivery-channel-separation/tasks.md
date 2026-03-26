# Tasks: Analysis Engine / Delivery Channel Separation

## Slice S1: Delivery Foundation

- [x] Define delivery-channel models and channel-specific context contracts
- [x] Introduce `ProgressSink` abstraction and Telegram implementation
- [x] Refactor worker progress flow to use the abstraction without changing UX
- [x] Keep queue/job serialization stable and covered by tests
- [x] Add focused tests for Telegram progress through the abstraction

## Follow-up Slices

- [x] S1b: migrate Telegram fields out of `AnalysisJob` — move `telegram_chat_id`,
      `telegram_message_id`, and `telegram_progress_message_id` from the core job
      model into `TelegramDeliveryContext`; update the router, worker, and all tests
      that construct `AnalysisJob` directly (prerequisite for a fully channel-neutral job shape)
- [x] S1b follow-up (PR #42): add model-level validator enforcing `telegram_context`
      is present for TELEGRAM jobs; add backward-compatibility shim that coerces old
      flat `telegram_*` Redis payloads into the new nested shape during rollout; clarify
      in processor docs that non-Telegram execution is deferred to later slices
- [ ] S2: shared submission/use-case layer
- [ ] S3: Telegram presenter split
- [ ] S4: web delivery foundation
- [ ] S5: web UI integration
