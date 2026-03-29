# Feature Spec: Compact Amenities Summary Output

## Goal

Replace the current flat `Amenities` block with a compact but more informative
summary that highlights concrete household setup, especially kitchen equipment,
without dumping the full raw inventory into Telegram.

## Problem

The current block only shows:

- a single `Key amenities` line
- a single `Missing or not included` line

That is too shallow for decisions about real stay comfort. In particular, a
listing with `Kitchen` should expose whether the kitchen is actually useful
(`refrigerator`, `microwave`, `cooking basics`, `dishes`, `kettle`, `toaster`)
instead of reducing everything to the generic word `Kitchen`.

## Scope

In scope:

- compact user-facing amenities block in Telegram output
- grouped summary lines derived from existing amenities evidence data
- deterministic rendering only; no new LLM behavior
- no full inventory dump

Out of scope:

- review/amenities comparison
- web UI rendering
- full grouped inventory output
- new provider integrations

## User-Facing Shape

The block should stay compact and render only non-empty sections.

Target structure:

1. `Amenities`
2. `Key amenities`
3. `Home comfort`
4. `Kitchen and dining`
5. `Outdoor and facilities`
6. `Missing or not included`

Example:

```text
Amenities:
Key amenities: Wi-Fi, Kitchen, Air conditioning, Washer, Parking, Pool
Home comfort: Bathtub, Hot water, Bed linens, TV
Kitchen and dining: Refrigerator, Microwave, Cooking basics, Dishes and silverware, Kettle, Toaster
Outdoor and facilities: Balcony or patio, Outdoor dining area, BBQ grill, Parking, Pool
Missing or not included:
- Heating
- Essentials
- Smoke alarm
- Carbon monoxide alarm
```

## Requirements

### R1. Concrete kitchen detail

When kitchen-related amenities are available, the block must surface concrete
kitchen equipment instead of only the generic `Kitchen` label.

### R2. Compact grouped format

The formatter must render grouped summary lines rather than a long raw list.

### R3. Deterministic mapping

The grouping must be derived from existing normalized amenities evidence data
and remain deterministic; no new LLM prompt or translation call may be added
for this feature.

### R4. Missing items remain explicit

Critical unavailable items must still appear in a dedicated
`Missing or not included` subsection.

### R5. Omit empty sections

Sections with no visible items must be omitted entirely.

## Acceptance Criteria

- Airbnb amenities evidence produces enough structured data to render grouped
  compact sections.
- Telegram formatter renders compact grouped lines for non-empty sections.
- Kitchen-related detail is visible when present.
- Existing reviews, price, and summary output remain intact.
- Tests cover mapping and formatting behavior.
