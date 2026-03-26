# Tasks: Analysis Engine / Delivery Channel Separation

## Slice S1: Delivery Foundation

- [x] Define delivery-channel models and channel-specific context contracts
- [x] Introduce `ProgressSink` abstraction and Telegram implementation
- [x] Refactor worker progress flow to use the abstraction without changing UX
- [x] Keep queue/job serialization stable and covered by tests
- [x] Add focused tests for Telegram progress through the abstraction

## Follow-up Slices

- [ ] S2: shared submission/use-case layer
- [ ] S3: Telegram presenter split
- [ ] S4: web delivery foundation
- [ ] S5: web UI integration
