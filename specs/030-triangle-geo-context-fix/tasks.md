# Tasks 030 - Triangle Geo Context Fix

## Status: complete

- [x] Reproduce and document the live `tri_angle` geo-context regression
- [x] Patch `src/adapters/airbnb.py` to normalize live `tri_angle` coordinates and subtitle-based location fields
- [x] Patch `src/analysis/service.py` to skip empty enrichment payloads in the prompt
- [x] Add regression tests for tri-angle location mapping and empty-enrichment prompt behavior
- [x] Run targeted tests
      - `python -m pytest tests/test_airbnb_extraction.py tests/test_analysis.py tests/test_job_processor.py -q`
      - `151 passed`
- [x] Deploy the fix and run a live smoke on the server
      - live smoke now shows normalized coordinates and non-empty Geoapify enrichment
      - final rendered message no longer claims `no nearby transport` / `zero nearby places`

## Follow-up captured

- AI summary still does not fully consume the richer review-corpus signals from the dedicated reviews actor.
  In the live smoke, the summary block could still emit a generic review-related risk while the separate
  reviews block correctly shows `Reviews: 14`. This should be handled as a separate follow-up slice.
