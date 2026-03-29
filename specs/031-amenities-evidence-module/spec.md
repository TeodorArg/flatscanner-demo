# Spec 031 - Amenities Evidence Module

## Problem

The pipeline currently treats amenities as a flat `listing.amenities: list[str]`
fallback. This loses the detailed amenity structure provided by Airbnb and
does not give the modular analysis system a reusable source of truth for:

- concrete available amenities
- concrete unavailable amenities
- safety-related gaps
- category-level amenity signals for later comparison modules

## Goal

Introduce the first provider-aware amenities source module that extracts
structured amenity evidence from raw payloads and returns a unified corpus
usable by later comparison modules.

## Scope

### In scope

- unified amenity corpus models
- amenities taxonomy / canonical key mapping
- Airbnb normalizer that flattens nested `amenities[].values[]`
- generic fallback normalizer using `listing.amenities`
- `AmenitiesEvidenceModule` with Airbnb-specific and generic variants
- registration in the live module runner
- focused tests for normalization and module output

### Out of scope

- user-facing amenities block
- cross-checking amenities against reviews
- booking.com amenities support
- fee / rules extraction
- photo-based amenity validation

## Acceptance Criteria

- Airbnb raw payload amenities are flattened into concrete amenity items rather
  than top-level group headers
- each normalized amenity item records:
  - canonical key
  - label
  - category
  - availability
  - source group
- the module returns:
  - available amenity keys
  - unavailable amenity keys
  - critical missing keys
  - categories present
- the generic fallback continues to work when only `listing.amenities` is available
- the live analysis runner can execute the module without changing Telegram output yet
