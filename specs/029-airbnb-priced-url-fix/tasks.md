# Tasks 029 - Airbnb Priced URL Fix

## Status: implementation complete (price completeness pass added) — PR pending

- [x] Reproduce and document the live `tri_angle` dated-price failure mode
- [x] Fix `src/adapters/airbnb.py` actor input for dated Airbnb URLs
      — canonical room URL in startUrls (no query params); explicit checkIn/checkOut; occupancy forwarding
- [x] Extend normalized `PriceInfo` with dated-stay details needed downstream
      — check_in, check_out, stay_nights, nightly_rate added to PriceInfo domain model
- [x] Improve analysis prompt price context for dated stays
      — build_prompt shows total + dates + nights + nightly rate for stay-period prices
- [x] Add exact stay-price block to Telegram output
      — _format_stay_price added; i18n keys: fmt.stay_price_label, fmt.stay_nights_label, fmt.nightly_rate_label
- [x] Add/extend tests for actor input, normalization, prompt, and formatter
      — tests/test_029_priced_url.py (46 new tests); updated test_airbnb_extraction.py
      — full suite: 1118 passed
- [x] Price completeness pass: breakDown fee fallback, breakDown amount fallback, service fee in prompt/formatter
      — airbnb.py: fee from breakDown.cleaningFee/serviceFee when top-level absent; amount fallback from breakDown.total/basePrice
      — service.py: service fee line added to build_prompt alongside cleaning fee
      — formatter.py + i18n: cleaning/service fee lines in stay-price block (fmt.cleaning_fee_label, fmt.service_fee_label)
      — 16 new tests in test_029_priced_url.py; full suite: 1134 passed
- [ ] Open PR and drive checks to green
- [ ] Deploy the merged fix to the server and run a live smoke
