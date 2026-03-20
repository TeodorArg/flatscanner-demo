# Feature Spec: Review Analysis Skill And Unified Corpus

## Context

P4 (`019-review-analysis-module`) established the first live reviews module, but it still uses a
provider-shaped `Review`/`ReviewsData` model and a generic sentiment-style output. The next product
step is to make reviews analysis reusable across providers and focused on concrete rental incidents:

- pests and insects
- broken or missing essentials
- mold, dampness, and smells
- temperature problems (too hot / too cold)
- host conflicts and disputes
- unusual or risky situations
- view from the window

The system will receive reviews from multiple listing sites in different payload shapes, so raw
provider comments must be normalized into a single corpus contract before AI analysis. The review
analysis prompt and heuristics should also be documented as a reusable repository skill so future
review-related work stays consistent.

## Scope

- Introduce a repository skill for review analysis under `skills/review-analysis/`.
- Define a unified provider-agnostic review corpus contract.
- Replace provider-shaped review extraction with provider-specific normalizers that produce the
  unified corpus.
- Define a stricter incident-oriented review analysis output contract.
- Keep the existing Telegram output unchanged in this phase; this task prepares the analysis layer.

## Out Of Scope

- Rendering review incidents in the final Telegram response.
- Booking-specific normalizer implementation.
- Review persistence beyond the existing raw payload store.
- Result cache and billing concerns.

## Unified Review Corpus

### UnifiedReviewComment

```python
@dataclass
class UnifiedReviewComment:
    source_provider: str
    source_comment_id: str | None = None
    review_date: str | None = None
    stay_start_date: str | None = None
    stay_end_date: str | None = None
    rating: float | None = None
    language: str | None = None
    reviewer_name: str | None = None
    reviewer_origin: str | None = None
    comment_text: str = ""
    host_response_text: str | None = None
    listing_title_at_review_time: str | None = None
    raw_label: str | None = None
```

### ReviewCorpus

```python
@dataclass
class ReviewCorpus:
    source_provider: str
    source_listing_id: str | None = None
    source_url: str | None = None
    total_review_count: int | None = None
    average_rating: float | None = None
    comments: list[UnifiedReviewComment] = field(default_factory=list)
```

### ReviewExtractionResult

```python
@dataclass
class ReviewExtractionResult:
    corpus: ReviewCorpus
    extracted_comment_count: int
    dropped_comment_count: int = 0
    warnings: list[str] = field(default_factory=list)
```

## Review Skill Contract

The repository skill must keep the prompt and workflow concise and evidence-first.

Mandatory analysis priorities:
- pests
- damage
- missing essentials
- mold / dampness / smells
- temperature issues
- cleanliness
- safety
- host conflict
- listing mismatch
- noise
- check-in / access
- window view

Mandatory result behavior:
- extract incidents, not generic sentiment only
- highlight recurring issues and unusual situations
- emphasize negative comments and disputes
- attach date and source comment index when the evidence supports it
- produce a conservative overall assessment with explicit confidence

## Acceptance Criteria

- `skills/review-analysis/` exists and documents the review-analysis workflow without excessive prose.
- A unified review corpus contract replaces the provider-shaped review model.
- Provider-specific normalizers output the unified corpus contract.
- The reviews analysis service accepts the unified corpus contract.
- Tests cover Airbnb normalization, generic fallback normalization, and the stricter output parsing contract.
