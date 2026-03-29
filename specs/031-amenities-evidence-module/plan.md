# Plan 031 - Amenities Evidence Module

1. Add a unified `AmenityCorpus` contract and an availability enum.
2. Define a small taxonomy for canonical amenity keys and categories, with
   conservative fallbacks for unknown labels.
3. Implement provider-specific Airbnb normalization from live `tri_angle`
   nested amenities payloads.
4. Implement a generic fallback normalizer from `listing.amenities`.
5. Add `AmenitiesEvidenceModule` and register it in the current analysis runner.
6. Add focused regression tests for corpus normalization and module output.
