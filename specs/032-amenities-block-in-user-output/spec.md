# Spec 032 - Amenities Block In User Output

## Problem

`AmenitiesEvidenceModule` now extracts structured amenity evidence, but the user
still does not see any dedicated amenities section in the final Telegram reply.

## Goal

Expose a compact user-facing amenities block based on the structured amenities
source module, without waiting for the later consistency/comparison modules.

## Scope

### In scope

- map `AmenitiesEvidenceResult` into a renderable analysis-result block
- preserve the block through translation without sending it to the LLM
- render a localized Telegram section with:
  - key amenities
  - critical missing amenities

### Out of scope

- claims-vs-reality comparison
- reviews cross-check
- web output changes
- scenario-fit or advanced amenity reasoning

## Acceptance Criteria

- when amenities evidence exists, Telegram output includes an amenities section
- the section is compact and deterministic
- the section shows a curated list of key available amenities
- the section shows critical missing amenities when present
- non-English outputs preserve the block correctly
