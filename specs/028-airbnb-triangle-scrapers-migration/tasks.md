# Tasks 028 - Airbnb Migration to Tri_angle Scrapers

## Status: in progress

### Slice 1 - Listing / Details / Price / Photos

- [x] Create spec, plan, and tasks files
- [x] Switch the default Airbnb listing actor to `tri_angle/airbnb-rooms-urls-scraper`
- [x] Adapt `src/adapters/airbnb.py` to the new listing actor input/output schema
- [x] Update Airbnb extraction tests for the new schema
- [x] Update durable backend docs for the new default listing actor
- [ ] Open PR for Slice 1 and drive checks to green

### Slice 2 - Dedicated Reviews Source

- [ ] Add dedicated `tri_angle/airbnb-reviews-scraper` configuration
- [ ] Introduce Airbnb review-source fetching via the dedicated reviews actor
- [ ] Update Airbnb review normalization/tests for the new reviews schema
- [ ] Update the reviews module to use the dedicated reviews source
- [ ] Open PR for Slice 2 and drive checks to green

### Final validation

- [ ] Run end-to-end smoke after both slices land
