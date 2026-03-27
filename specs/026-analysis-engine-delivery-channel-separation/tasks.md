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
- [x] S2: shared submission/use-case layer — `src/application/analysis.py` with
      `submit_analysis_request` and `run_analysis_job`; router and worker updated to
      call the use-case layer; 10 focused tests added in `tests/test_analysis_use_cases.py`
- [x] S3: Telegram presenter split - `process_job` now delegates final Telegram
      formatting + delivery through `TelegramAnalysisPresenter`; the
      application layer forwards an optional `result_presenter`; focused tests
      cover the presenter seam and full suite remains green
- [x] S4: web delivery foundation — `WebDeliveryContext` added to domain/delivery;
      `web_context` field added to `AnalysisJob`; `src/web/` package with
      `WebSubmitRequest/Response`, `WebJobStatusResponse`, `WebAnalysisResultResponse`
      models, `WebProgressSink` and `WebAnalysisPresenter` no-op stubs, and
      a FastAPI router with `POST /web/submit` (501 placeholder — no real enqueuing),
      `GET /web/status/{job_id}` (200 stub, persistence deferred),
      `GET /web/result/{job_id}` (200 stub, storage deferred);
      processor updated to use no-op path for WEB-channel jobs;
      web router registered in `src/app/main.py`;
      focused tests in `tests/test_web_delivery.py` cover domain models, stubs,
      read-model contracts, and honest placeholder endpoint behavior
- [ ] S5: web UI integration

## Follow-up (deferred, no runtime change)

- [ ] `UnsupportedProviderError` layering — this exception is currently raised inside
  `src/jobs/processor.py`, which is below the use-case layer.  Once S3/S4 land and
  the use-case layer owns more of the error surface, consider re-raising it (or a
  channel-neutral wrapper) from `run_analysis_job` so callers don't need to import
  from `src.jobs` to handle it.  No change needed until a second channel is wired up.
