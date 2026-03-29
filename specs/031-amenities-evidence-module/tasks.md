# Tasks 031 - Amenities Evidence Module

## Status: complete

- [x] Add unified amenity corpus models and taxonomy
- [x] Implement Airbnb amenities normalizer for nested `tri_angle` payloads
- [x] Implement generic amenities normalizer fallback
- [x] Add provider-aware `AmenitiesEvidenceModule`
- [x] Register the module in the live runner
- [x] Add focused tests for normalization and module output
- [x] Run targeted tests
      - `python -m pytest tests/test_amenities_evidence_module.py tests/test_analysis_module_framework.py tests/test_job_processor.py -q`
      - `73 passed`

## Follow-up captured

- User-facing amenities block is intentionally deferred.
- `ListingClaimsModule` and `AmenitiesConsistencyModule` should consume this
  corpus in the next slices instead of re-parsing raw amenities again.
