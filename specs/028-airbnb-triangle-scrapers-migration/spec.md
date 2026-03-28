# Spec 028 - Airbnb Migration to Tri_angle Scrapers

## Problem

The current Airbnb actor (`curious_coder~airbnb-scraper`) was sufficient for the
MVP, but it is no longer a strong fit for the post-MVP engine:

- dated Airbnb URLs do not reliably yield usable price data
- listing, pricing, photos, and reviews are coupled in one unstable payload
- future photo and review modules need more specialized source contracts

Live validation showed that even with `scrapeDetail=True` and explicit stay dates,
the current actor still returned `pricing = null` and `costPerNight = null` for
dated Airbnb URLs. Continuing to optimize around that actor would add complexity
without fixing the root issue.

## Goal

Migrate Airbnb ingestion to a pair of specialized `tri_angle` actors:

1. `tri_angle~airbnb-rooms-urls-scraper`
   - listing details
   - dated price data
   - photos
   - host / amenities / rules
2. `tri_angle~airbnb-reviews-scraper`
   - dedicated review corpus for the reviews module

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

Migrate reviews ingestion to `tri_angle~airbnb-reviews-scraper` and make the
Airbnb reviews module consume the dedicated review payload instead of assuming
reviews come from the listing actor.

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
- Slice 2 lands with the Airbnb reviews module backed by the dedicated
  `tri_angle` reviews actor.
- The repository memory is updated to reflect the new actor split and why it
  exists.
