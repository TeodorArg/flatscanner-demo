# Spec 040 - Remove Current Amenities Module

## Summary

Remove the current amenities module and every user-facing/runtime surface tied
to it so the project returns to the pre-amenities baseline before a redesign.

## Scope

- delete the current amenities analysis module implementation
- remove amenities transport/result models from the runtime path
- remove Telegram formatting and i18n paths dedicated to the amenities block
- remove amenities-specific tests
- remove obsolete feature memory/spec folders created for the old amenities work

## Out Of Scope

- redesigning a replacement amenities architecture
- changing the base `listing.amenities` adapter field used by the generic AI summary
- introducing new amenity-related docs or UI

## Acceptance

- no amenities module is registered in the job processor
- final Telegram output contains no dedicated amenities block
- `AnalysisResult` no longer carries amenities-specific transport fields
- amenities-specific tests/specs are removed
- the test suite passes after the removal
