# Tasks 029 - Airbnb Priced URL Fix

## Status: complete

- [x] Reproduce and document the live `tri_angle` dated-price failure mode
      - canonical room URL in `startUrls` was required; dated query-string URLs caused the actor to return the no-price fallback label
- [x] Fix `src/adapters/airbnb.py` actor input for dated Airbnb URLs
      - canonical room URL in `startUrls` (no query params)
      - explicit `checkIn` / `checkOut`
      - occupancy forwarding from URL query (`adults`, `children`, `infants`, `pets`)
- [x] Extend normalized `PriceInfo` with dated-stay details needed downstream
      - `check_in`, `check_out`, `stay_nights`, `nightly_rate`
- [x] Improve analysis prompt price context for dated stays
      - total stay price
      - stay window and number of nights
      - nightly rate when derivable
      - service / cleaning fee lines when present
- [x] Add exact stay-price block to Telegram output
      - exact stay dates
      - total amount
      - nightly rate
      - service / cleaning fee lines when present
- [x] Add and extend tests for actor input, normalization, prompt, and formatter
      - `tests/test_029_priced_url.py`
      - updated `tests/test_airbnb_extraction.py`
      - full suite: `1134 passed`
- [x] Open PR and drive checks to green
      - PR [#48](https://github.com/alexgoodman53/flatscanner/pull/48)
- [x] Deploy the merged fix to the server and run a live smoke
      - VPS stack recreated successfully
      - live smoke confirmed exact stay price now appears for a priced Airbnb URL
