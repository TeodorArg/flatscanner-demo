"""Review domain models.

``Review`` represents a single guest review extracted from a provider raw payload.
``ReviewsData`` bundles a list of reviews with aggregate metadata (total count,
average rating) for use by the reviews analysis module.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Review:
    """A single guest review extracted from a raw provider payload.

    All fields are optional because different providers and scraper actor
    versions expose different subsets of review data.
    """

    reviewer_name: str | None = None
    date: str | None = None
    # Per-review rating when the provider exposes it (e.g. Airbnb sub-ratings).
    rating: float | None = None
    text: str | None = None


@dataclass
class ReviewsData:
    """Collection of extracted reviews with aggregate metadata.

    ``total_count`` is the provider-reported total, which may exceed
    ``len(reviews)`` when only a sample was scraped.  ``average_rating``
    is the listing-level aggregate, not the mean of ``reviews[*].rating``.
    """

    reviews: list[Review] = field(default_factory=list)
    # Provider-reported total (may differ from len(reviews)).
    total_count: int = 0
    # Listing-level aggregate rating (e.g. Airbnb's starRating).
    average_rating: float | None = None
