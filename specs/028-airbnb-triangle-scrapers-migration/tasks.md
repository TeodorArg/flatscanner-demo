# Tasks 028 - Airbnb Migration to Tri_angle Scrapers

## Status: in progress

### Slice 1 - Listing / Details / Price / Photos

- [x] Create spec, plan, and tasks files
- [x] Switch the default Airbnb listing actor to `tri_angle~airbnb-rooms-urls-scraper`
- [x] Adapt `src/adapters/airbnb.py` to the new listing actor input/output schema
- [x] Update Airbnb extraction tests for the new schema
- [x] Update durable backend docs for the new default listing actor
- [x] Follow-up: fix actor ID to tilde form (slash form returns 404 in Apify client)
- [x] Follow-up: parse check_in/check_out from URL and pass as checkIn/checkOut actor input
- [x] Follow-up: normalize tri_angle price object (label/price/basePrice.price) into PriceInfo
- [x] Follow-up: fix photos field — live actor uses `images`, not `photos`
- [x] Follow-up: fix dated-stay price period — derive from qualifier (night/week/month/stay) instead of hardcoding 'night'; use discountedPrice as primary amount source
- [x] Follow-up: fix slash-form actor IDs in docstrings and docs (must use tilde form in runtime config)
- [x] Open PR for Slice 1 and drive checks to green

### Slice 2 - Dedicated Reviews Source

- [ ] Add dedicated `tri_angle~airbnb-reviews-scraper` configuration
- [ ] Introduce Airbnb review-source fetching via the dedicated reviews actor
- [ ] Update Airbnb review normalization/tests for the new reviews schema
- [ ] Update the reviews module to use the dedicated reviews source
- [ ] Open PR for Slice 2 and drive checks to green

### Final validation

- [ ] Run end-to-end smoke after both slices land
