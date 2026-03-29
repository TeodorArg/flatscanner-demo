# Spec 030 - Triangle Geo Context Fix

## Problem

After the Airbnb migration to `tri_angle~airbnb-rooms-urls-scraper`, the live
pipeline sometimes generates obviously wrong location conclusions such as:

- no nearby public transport within 500 meters
- zero nearby places within 500 meters

even for listings in dense urban neighborhoods.

Live validation showed two regressions:

1. the Airbnb adapter still normalizes location using the old payload shape and
   misses `tri_angle` coordinates and subtitle-based location fields
2. empty Geoapify enrichment results (`{}`) are rendered in the AI prompt as
   real zero-count facts instead of being omitted

## Goal

Restore correct geo-context handling for `tri_angle` Airbnb listings by:

1. normalizing coordinates and basic location labels from the live `tri_angle`
   payload shape
2. omitting empty enrichment payloads from the analysis prompt so “no data”
   never becomes “zero nearby places”

## Scope

### In scope

- `src/adapters/airbnb.py` location normalization for live `tri_angle` payloads
- `src/analysis/service.py` prompt guard for empty enrichment payloads
- targeted regression tests for both code paths

### Out of scope

- new location providers
- richer neighborhood inference
- Web UI changes
- changes to the review module

## Acceptance Criteria

- `tri_angle` payloads with `coordinates` and `locationSubtitle` produce a
  normalized listing with non-empty coordinates and basic city/country fields
- Geo prompt context is omitted when an enrichment provider returns an empty
  dict because no coordinates were available
- legitimate zero-count enrichment payloads are still preserved when the
  provider returns a non-empty structured result
