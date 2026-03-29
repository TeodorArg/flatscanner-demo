# Spec 028 - Airbnb Migration to Tri_angle Scrapers

## Problem

The current Airbnb actor (`curious_coder~airbnb-scraper`) was sufficient for the
MVP, but it was no longer a strong fit for the post-MVP engine:

- dated Airbnb URLs did not reliably yield usable price data
- listing, pricing, photos, and reviews were coupled in one unstable payload
- future photo and review modules needed more specialized source contracts

Live validation showed that even with `scrapeDetail=True` and explicit stay dates,
the current actor still returned `pricing = null` and `costPerNight = null` for
dated Airbnb URLs. Continuing to optimize around that actor would add complexity
without fixing the root issue.

## Goal

Migrate Airbnb ingestion to a specialized `tri_angle` room-URL actor while
introducing a dedicated review-source seam for the reviews module.

1. `tri_angle~airbnb-rooms-urls-scraper`
   - listing details
   - dated price data
   - photos
   - host / amenities / rules
2. a dedicated Airbnb review-source seam
   - decouples the reviews module from any one listing actor payload

## Scope

This feature is intentionally split into narrow slices.

### Slice 1

Replace the current listing/detail Airbnb actor with
`tri_angle~airbnb-rooms-urls-scraper` and adapt normalization for:

- listing title/description/location
- price fields
- host / amenities
- photo payload preservation in raw data

### Slice 2

Refactor review ingestion behind a dedicated Airbnb review-source abstraction so
the reviews module no longer assumes reviews always come from the listing
payload.

## Non-goals

- No Booking.com migration in this task
- No calendar search for nearest 1-night / 1-week / 1-month windows
- No price intelligence / comparables engine
- No photo-analysis module implementation yet
- No Web UI changes

## Acceptance Criteria

- Slice 1 lands with the default Airbnb listing actor changed to the `tri_angle`
  room-URL actor and existing Telegram analysis continues to work.
- Slice 1 yields a better source contract for dated Airbnb pricing than the
  current actor path.
- Slice 2 lands with the Airbnb reviews module backed by a dedicated review
  source abstraction rather than a hard-coded listing payload path.
- The repository memory is updated to reflect the new listing actor split and
  the review-source abstraction.
