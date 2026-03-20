# Implementation Plan: 019-review-analysis-module

## New files

| File | Purpose |
|---|---|
| `src/domain/review.py` | `Review` and `ReviewsData` domain models |
| `src/analysis/reviews/__init__.py` | reviews sub-package |
| `src/analysis/reviews/extractor.py` | `ReviewExtractor` Protocol + `ReviewAnalysisOutput` |
| `src/analysis/reviews/airbnb_extractor.py` | `AirbnbReviewExtractor` — extracts from raw Airbnb payload |
| `src/analysis/reviews/generic_extractor.py` | `GenericReviewExtractor` — uses listing metadata |
| `src/analysis/reviews/service.py` | `ReviewAnalysisService` — AI-backed review analysis |
| `src/analysis/modules/reviews.py` | `ReviewsResult`, `AirbnbReviewsModule`, `GenericReviewsModule` |
| `tests/test_reviews_module.py` | Focused unit tests for all new components |

## Changed files

| File | Change |
|---|---|
| `src/analysis/__init__.py` | Add new symbols to `__all__` |
| `src/analysis/modules/__init__.py` | Import new module for discoverability |
| `src/jobs/processor.py` | Register `AirbnbReviewsModule` and `GenericReviewsModule` |
| `tests/test_job_processor.py` | Integration test for reviews module registration |
| `specs/019-review-analysis-module/tasks.md` | Task state tracking |

## Approach

Additive only — no changes to `AnalysisService`, `AISummaryModule`, `AnalysisResult`, or the
Telegram formatter. The reviews module registers alongside `AISummaryModule` in `process_job`
and its `ReviewsResult` is available in `module_results` for future consumption.

## Airbnb raw payload review fields

The Apify `curious_coder~airbnb-scraper` actor returns reviews when `scrapeReviews: True`.
Typical shape (defensive extraction handles variations):

```json
{
  "reviews": [
    {
      "reviewer": { "firstName": "Alice" },
      "createdAt": "2024-06-01",
      "rating": 5,
      "comments": "Great place!"
    }
  ],
  "reviewsCount": 42,
  "starRating": 4.8
}
```

Alternative field names handled:
- `reviews` or `feedbacks`
- `reviewer.firstName` or `reviewer.name` or `authorName`
- `createdAt` or `localizedDate` or `date`
- `comments` or `text` or `body`
- `rating` per review (may be absent)

## AI review prompt strategy

When reviews are available, `ReviewAnalysisService` sends up to 10 review texts (each capped
at 300 chars) plus aggregate metadata. Response is a JSON object:

```json
{
  "sentiment_summary": "...",
  "common_themes": ["...", "..."],
  "concerns": ["...", "..."]
}
```

Missing or invalid fields are defaulted gracefully (empty list, empty string).
