# Tasks 032 - Amenities Block In User Output

## Status: complete

- [x] Add `AmenitiesInsightsBlock` to the analysis result schema
- [x] Map `AmenitiesEvidenceResult` into the final result in the job processor
- [x] Preserve the block through translation
- [x] Render the amenities block in Telegram output
- [x] Add focused tests
- [x] Run targeted tests
      - `python -m pytest tests/test_amenities_output_block.py tests/test_telegram_formatter.py tests/test_translation_service.py tests/test_job_processor.py -q`
      - `116 passed`

## Follow-up captured

- The current block is intentionally deterministic and source-only.
- `ListingClaimsModule` and `AmenitiesConsistencyModule` should upgrade this
  block later from "what amenities are declared" to "what is claimed vs.
  supported or contradicted".
