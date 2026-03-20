"""Unified review corpus models.

Provider-agnostic models for normalized review data. These replace the
provider-shaped ``Review``/``ReviewsData`` models as the canonical input
contract for the review analysis service.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UnifiedReviewComment:
    """A single normalized guest review comment.

    All optional fields may be ``None`` when the source provider does not
    expose them or when the raw payload omits them.
    """

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


@dataclass
class ReviewCorpus:
    """Unified review corpus for a single listing.

    Aggregates all normalized comments for one listing together with
    provider-level metadata.
    """

    source_provider: str
    source_listing_id: str | None = None
    source_url: str | None = None
    total_review_count: int | None = None
    average_rating: float | None = None
    comments: list[UnifiedReviewComment] = field(default_factory=list)


@dataclass
class ReviewExtractionResult:
    """Result of a review normalization operation.

    Wraps a ``ReviewCorpus`` with extraction bookkeeping so callers can
    detect dropped or malformed records without raising exceptions.
    """

    corpus: ReviewCorpus
    extracted_comment_count: int
    dropped_comment_count: int = 0
    warnings: list[str] = field(default_factory=list)
