# Spec 029 - Airbnb Priced URL Fix

## Problem

After the migration to `tri_angle~airbnb-rooms-urls-scraper`, dated Airbnb URLs
still often reach the actor without usable price output in the live pipeline.

Live validation showed the current adapter path sends the full dated Airbnb URL
inside `startUrls` while also forwarding explicit `checkIn` / `checkOut`.
For the `tri_angle` rooms actor this often yields the fallback label:

- "To get prices, specify check-in and check-out date in the input..."

As a result:

- `listing.price` stays empty for many dated URLs
- the AI price block falls back to `Unknown`
- the user does not see the exact stay price that was already present in the
  original Airbnb link context

## Goal

Make Airbnb price handling work reliably for dated Airbnb URLs by:

1. sending the actor the canonical room URL without query params
2. forwarding stay dates and occupancy explicitly from the Airbnb URL query
3. normalizing richer stay-price details from the `tri_angle` price object
4. surfacing exact stay-price information in the final user output

## Scope

This task is intentionally narrow and limited to the current Airbnb rooms actor.

### In scope

- sanitize `startUrls` for `tri_angle~airbnb-rooms-urls-scraper`
- forward `check_in` / `check_out`
- forward occupancy query params when present (`adults`, `children`, `infants`, `pets`)
- extend normalized price data with stay-level details when available
- improve analysis prompt price context for dated stays
- add a user-facing exact price block to Telegram output when stay pricing exists
- add regression tests for the new actor-input and price-output behavior

### Out of scope

- nearest available interval search
- market comparables / price intelligence
- Booking.com pricing
- Web UI changes
- replacing the `tri_angle` actor

## Acceptance Criteria

- For Airbnb URLs with `check_in` and `check_out`, the adapter sends the actor:
  - canonical room URL in `startUrls`
  - explicit `checkIn` / `checkOut`
  - explicit occupancy fields when present
- When the actor returns priced output, `listing.price` is populated reliably.
- Stay-level price details (dates / nights / nightly rate / fees when available)
  are preserved in normalized form.
- The analysis prompt receives better structured price context for dated stays.
- Telegram output shows an exact stay-price block when stay pricing is known.
- Undated URLs continue to work without regressions.
