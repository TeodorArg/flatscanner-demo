# Technical Plan: Compact Amenities Summary Output

## Approach

Keep the feature narrow by reusing the existing `AmenitiesEvidenceResult` and
expanding only the transport object passed into the formatter.

### Data path

1. `AmenitiesEvidenceModule` already yields canonical available/unavailable keys
   plus the full normalized corpus.
2. `process_job` will derive compact grouped sections from the corpus.
3. `AnalysisResult.amenities_insights` will carry those grouped sections.
4. Translation preserves the structure unchanged.
5. Telegram formatter renders grouped summary lines using i18n labels.

## Planned Changes

### 1. Result schema

Extend `AmenitiesInsightsBlock` with deterministic grouped sections.

### 2. Processor mapping

Use the normalized amenity corpus to build:

- `key amenities`
- `home comfort`
- `kitchen and dining`
- `outdoor and facilities`
- `critical missing`

### 3. Formatter

Render the compact grouped variant and omit empty sections.

### 4. Catalog

Add section labels and missing amenity labels needed by the grouped output.

### 5. Tests

Update/add focused tests for:

- grouped mapping from amenities evidence
- formatter rendering
- no regression on translation preservation

## Risks

- Overlapping categories can duplicate some amenities between the headline and
  grouped lines. This is acceptable for the compact Telegram summary as long as
  the block stays readable.
- Unknown provider-specific keys may fall back to prettified labels when no
  catalog entry exists.

## Validation

- targeted pytest for amenities output + formatter + processor
- live smoke on VPS using the known Palermo Airbnb listing
