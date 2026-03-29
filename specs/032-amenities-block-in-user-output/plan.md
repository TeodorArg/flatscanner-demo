# Plan 032 - Amenities Block In User Output

1. Add an `AmenitiesInsightsBlock` to `AnalysisResult`.
2. Map `AmenitiesEvidenceResult` into that block in the job processor.
3. Preserve the block through translation without sending amenity keys to the LLM.
4. Render a compact localized amenities section in the Telegram formatter.
5. Add focused tests for mapping, translation preservation, and formatter output.
