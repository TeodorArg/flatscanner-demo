# Tasks: 019-review-analysis-module

## Status: in-progress

| # | Task | State |
|---|---|---|
| 1 | Create spec, plan, tasks files | done |
| 2 | `src/domain/review.py` — `Review` + `ReviewsData` | done |
| 3 | `src/analysis/reviews/extractor.py` — `ReviewExtractor` Protocol + `ReviewAnalysisOutput` | done |
| 4 | `src/analysis/reviews/airbnb_extractor.py` — `AirbnbReviewExtractor` | done |
| 5 | `src/analysis/reviews/generic_extractor.py` — `GenericReviewExtractor` | done |
| 6 | `src/analysis/reviews/service.py` — `ReviewAnalysisService` | done |
| 7 | `src/analysis/modules/reviews.py` — `ReviewsResult`, `AirbnbReviewsModule`, `GenericReviewsModule` | done |
| 8 | Update `src/analysis/__init__.py` exports | done |
| 9 | Wire reviews modules into `src/jobs/processor.py` | done |
| 10 | `tests/test_reviews_module.py` — focused unit tests | done |
| 11 | Add reviews module integration tests in `tests/test_job_processor.py` | done |
| 12 | All tests pass | done |
| 13 | `AirbnbReviewsModule` non-blocking: AI failures degrade to metadata-only `ReviewsResult` | done |
| 14 | `AnalysisContext.raw_payload` always populated from `adapter_result.raw` (independent of `raw_payload_repo`) | done |
