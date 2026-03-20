# Feature Spec: Reviews Analysis Module (P4)

## Context

This is P4 of the post-MVP migration defined in `specs/015-post-mvp-architecture-foundation/spec.md`
and ADR 004.

P3 delivered the analysis module framework: `ModuleRegistry`, `ModuleRunner`, and the generic
`AISummaryModule`. P4 adds the first specialist module — a provider-aware reviews analysis slice
that extracts review data from raw payloads, runs an AI analysis over the extracted reviews, and
produces a `ReviewsResult` alongside the existing `AISummaryResult`.

The Telegram output is not changed in this PR; the reviews module runs silently alongside the
AI summary module and its result is available in the `module_results` list for future use.

## Scope

- `Review` and `ReviewsData` domain models in `src/domain/review.py`.
- `ReviewExtractor` protocol in `src/analysis/reviews/extractor.py`.
- `AirbnbReviewExtractor` in `src/analysis/reviews/airbnb_extractor.py`: extracts reviews
  from the Airbnb raw payload (Apify actor output). Handles the `reviews` / `feedbacks` array
  and falls back gracefully when the field is absent.
- `GenericReviewExtractor` in `src/analysis/reviews/generic_extractor.py`: constructs a
  `ReviewsData` from listing-level metadata (`rating`, `review_count`) when no raw payload
  is available or the provider is not Airbnb.
- `ReviewAnalysisService` in `src/analysis/reviews/service.py`: builds a prompt from
  `ReviewsData`, calls OpenRouter, and parses the response into a `ReviewAnalysisOutput`.
- `ReviewsResult` dataclass (extends `ModuleResult`) in `src/analysis/modules/reviews.py`.
- `AirbnbReviewsModule` (provider-specific, `supported_providers={ListingProvider.AIRBNB}`)
  and `GenericReviewsModule` (generic, `supported_providers=frozenset()`) in the same file.
- Both modules registered in `process_job` next to `AISummaryModule`.
- Focused tests in `tests/test_reviews_module.py`.
- Integration test coverage in `tests/test_job_processor.py`.

## Out of Scope

- Exposing review insights in the Telegram formatter (P4+).
- Persisting `ReviewsResult` to the database (P5+).
- Analysis result cache (P5).

## Contracts

### Review domain models

```python
@dataclass
class Review:
    reviewer_name: str | None = None
    date: str | None = None
    rating: float | None = None
    text: str | None = None

@dataclass
class ReviewsData:
    reviews: list[Review] = field(default_factory=list)
    total_count: int = 0
    average_rating: float | None = None
```

### ReviewExtractor (Protocol)

```python
class ReviewExtractor(Protocol):
    def extract(
        self,
        payload: dict[str, Any],
        listing: NormalizedListing,
    ) -> ReviewsData: ...
```

### ReviewAnalysisOutput

```python
@dataclass
class ReviewAnalysisOutput:
    sentiment_summary: str
    common_themes: list[str]
    concerns: list[str]
```

### ReviewsResult

```python
@dataclass
class ReviewsResult(ModuleResult):
    review_count: int | None = None
    average_rating: float | None = None
    sentiment_summary: str | None = None
    common_themes: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
```

### AirbnbReviewsModule

- `name = "reviews"`
- `supported_providers = frozenset({ListingProvider.AIRBNB})`
- `run(ctx)` extracts reviews from `ctx.raw_payload.payload` (via `AirbnbReviewExtractor`);
  falls back to `GenericReviewExtractor` when `ctx.raw_payload` is `None`.
- Runs `ReviewAnalysisService.analyse(reviews_data)` when at least one review text is present;
  skips AI call and returns metadata-only result otherwise.

### GenericReviewsModule

- `name = "reviews"`
- `supported_providers = frozenset()` (generic)
- `run(ctx)` uses `GenericReviewExtractor` to build `ReviewsData` from listing metadata.
- No AI call; returns a `ReviewsResult` with count and rating only.

### Live pipeline wiring

`process_job` registers both modules:
```python
registry.register(AirbnbReviewsModule(review_service))
registry.register(GenericReviewsModule())
```

The registry resolves `AirbnbReviewsModule` for Airbnb listings and `GenericReviewsModule` for
unknown providers. The resulting `ReviewsResult` is present in `module_results` but not yet
consumed by the formatter.

## Acceptance Criteria

- All new files compile and are importable.
- Existing tests pass unchanged.
- Focused tests cover: Review/ReviewsData construction, Airbnb extractor field mapping and
  graceful degradation, generic extractor metadata mapping, `ReviewAnalysisService` prompt
  building and response parsing, `AirbnbReviewsModule` and `GenericReviewsModule` contracts,
  and end-to-end roundtrip through registry+runner.
- Integration tests confirm the reviews module is registered and its result appears in
  `module_results` alongside `AISummaryResult`.
- Telegram output is unchanged (existing integration test assertions continue to pass).
