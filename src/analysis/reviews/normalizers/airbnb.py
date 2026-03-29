"""Airbnb review normalizer.

``AirbnbReviewNormalizer`` maps Airbnb review data into the unified
``ReviewCorpus`` contract.  Field extraction is deliberately defensive:
all lookups fall back gracefully when a key is absent or holds an
unexpected type.

Two input shapes are supported:

1. **Listing payload** (legacy ``curious_coder`` actor or listing actor
   with embedded reviews) — use ``normalize()``:

   .. code-block:: json

       {
         "reviews": [
           {
             "id": "abc123",
             "reviewer": {"firstName": "Alice", "location": "London"},
             "createdAt": "2024-06-01",
             "rating": 5,
             "comments": "Great place!",
             "response": "Thanks for staying!"
           }
         ],
         "reviewsCount": 42,
         "starRating": 4.8
       }

2. **Flat review items** from one-item-per-review sources — use
   ``normalize_from_actor_items()``:

   .. code-block:: json

       [
         {
           "id": "abc123",
           "language": "en",
           "text": "Great place!",
           "localizedDate": "March 2024",
           "createdAt": "2024-03-15",
           "localizedReviewerLocation": "New York",
           "reviewer": {"firstName": "Alice"},
           "rating": 5,
           "response": "Thanks for staying!",
           "reviewHighlight": null
         }
       ]

Alternative field names handled per review item:
- Reviews array (``normalize()`` only): ``reviews`` or ``feedbacks``
- Comment id: ``id`` or ``reviewId``
- Reviewer name: ``reviewer.firstName``, ``reviewer.name``, ``authorName``
- Reviewer origin: ``reviewer.location``, ``reviewer.hometown``,
  ``localizedReviewerLocation`` (top-level review field when present)
- Date: ``createdAt``, ``localizedDate``, ``date``
- Review text: ``comments``, ``text``, ``body``
- Host response: ``response``, ``hostReply``, ``hostResponse``
- Language: ``language``, ``languageTag``
- Per-review rating: ``rating`` (may be absent)
"""

from __future__ import annotations

from typing import Any

from src.domain.review_corpus import ReviewCorpus, ReviewExtractionResult, UnifiedReviewComment

_SOURCE_PROVIDER = "airbnb"


# ---------------------------------------------------------------------------
# Field helpers
# ---------------------------------------------------------------------------


def _str_or_none(val: Any) -> str | None:
    """Return *val* as a stripped string, or ``None`` if falsy or not a str."""
    if isinstance(val, str) and val.strip():
        return val.strip()
    return None


def _float_or_none(val: Any) -> float | None:
    """Return *val* as float, or ``None`` on failure."""
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _extract_comment_id(item: dict[str, Any]) -> str | None:
    val = item.get("id") or item.get("reviewId")
    return _str_or_none(str(val)) if val is not None else None


def _extract_reviewer_name(item: dict[str, Any]) -> str | None:
    reviewer = item.get("reviewer")
    if isinstance(reviewer, dict):
        name = reviewer.get("firstName") or reviewer.get("name")
        if name:
            return _str_or_none(str(name))
    return _str_or_none(item.get("authorName"))


def _extract_reviewer_origin(item: dict[str, Any]) -> str | None:
    reviewer = item.get("reviewer")
    if isinstance(reviewer, dict):
        origin = (
            _str_or_none(reviewer.get("location"))
            or _str_or_none(reviewer.get("hometown"))
        )
        if origin:
            return origin
    # Some review sources surface reviewer location at the top level.
    return _str_or_none(item.get("localizedReviewerLocation"))


def _extract_date(item: dict[str, Any]) -> str | None:
    return (
        _str_or_none(item.get("createdAt"))
        or _str_or_none(item.get("localizedDate"))
        or _str_or_none(item.get("date"))
    )


def _extract_text(item: dict[str, Any]) -> str:
    return (
        _str_or_none(item.get("comments"))
        or _str_or_none(item.get("text"))
        or _str_or_none(item.get("body"))
        or ""
    )


def _extract_host_response(item: dict[str, Any]) -> str | None:
    return (
        _str_or_none(item.get("response"))
        or _str_or_none(item.get("hostReply"))
        or _str_or_none(item.get("hostResponse"))
    )


def _extract_language(item: dict[str, Any]) -> str | None:
    return (
        _str_or_none(item.get("language"))
        or _str_or_none(item.get("languageTag"))
    )


def _parse_comment(item: Any) -> UnifiedReviewComment | None:
    """Parse a single review dict.  Returns ``None`` for non-dict inputs."""
    if not isinstance(item, dict):
        return None
    return UnifiedReviewComment(
        source_provider=_SOURCE_PROVIDER,
        source_comment_id=_extract_comment_id(item),
        review_date=_extract_date(item),
        rating=_float_or_none(item.get("rating")),
        language=_extract_language(item),
        reviewer_name=_extract_reviewer_name(item),
        reviewer_origin=_extract_reviewer_origin(item),
        comment_text=_extract_text(item),
        host_response_text=_extract_host_response(item),
        listing_title_at_review_time=_str_or_none(item.get("listingTitle")),
        raw_label=_str_or_none(item.get("label")),
    )


# ---------------------------------------------------------------------------
# Normalizer
# ---------------------------------------------------------------------------


class AirbnbReviewNormalizer:
    """Normalizes Airbnb review data into a unified ``ReviewCorpus``.

    Usage::

        normalizer = AirbnbReviewNormalizer()

        # From listing payload (embedded reviews array):
        result = normalizer.normalize(raw_payload, listing)

        # From flat per-review actor items:
        result = normalizer.normalize_from_actor_items(items, listing)

        corpus = result.corpus
    """

    def normalize(
        self,
        payload: dict[str, Any],
        listing: Any,  # NormalizedListing — kept as Any to avoid circular import
    ) -> ReviewExtractionResult:
        """Normalize a listing payload dict into a ``ReviewExtractionResult``.

        Expects reviews embedded under a ``reviews`` or ``feedbacks`` key in
        *payload*, along with optional aggregate fields ``reviewsCount`` and
        ``starRating``.

        Parameters
        ----------
        payload:
            Raw Apify actor item dict (the ``payload`` field of ``RawPayload``).
        listing:
            Normalized listing; used to fall back on listing-level metadata
            for ``total_review_count`` and ``average_rating``.

        Returns
        -------
        ReviewExtractionResult
            Always returns a valid result; empty corpus when no review data.
        """
        raw_reviews = payload.get("reviews") or payload.get("feedbacks")
        comments: list[UnifiedReviewComment] = []
        dropped = 0
        if isinstance(raw_reviews, list):
            for item in raw_reviews:
                parsed = _parse_comment(item)
                if parsed is not None:
                    comments.append(parsed)
                else:
                    dropped += 1

        # total_review_count
        _rc1 = payload.get("reviewsCount")
        _rc2 = payload.get("reviewCount")
        raw_count = _rc1 if _rc1 is not None else _rc2
        if raw_count is not None:
            try:
                total_count: int | None = int(raw_count)
            except (TypeError, ValueError):
                total_count = len(comments)
        elif listing is not None and getattr(listing, "review_count", None) is not None:
            total_count = listing.review_count
        else:
            total_count = len(comments)

        # average_rating
        raw_rating = payload.get("starRating") or payload.get("rating")
        average_rating = _float_or_none(raw_rating)
        if average_rating is None and listing is not None:
            average_rating = getattr(listing, "rating", None)

        source_id = getattr(listing, "source_id", None) if listing is not None else None
        source_url = getattr(listing, "source_url", None) if listing is not None else None

        corpus = ReviewCorpus(
            source_provider=_SOURCE_PROVIDER,
            source_listing_id=str(source_id) if source_id is not None else None,
            source_url=source_url,
            total_review_count=total_count,
            average_rating=average_rating,
            comments=comments,
        )
        return ReviewExtractionResult(
            corpus=corpus,
            extracted_comment_count=len(comments),
            dropped_comment_count=dropped,
        )

    def normalize_from_actor_items(
        self,
        items: list[Any],
        listing: Any,  # NormalizedListing — kept as Any to avoid circular import
    ) -> ReviewExtractionResult:
        """Normalize a flat list of review items from per-review sources.

        Some sources return one dict per review (unlike the listing actor
        which embeds reviews under a ``reviews`` key in the listing payload).
        Aggregate metadata (total review count, average rating) is sourced
        from the listing because flat per-review sources usually do not
        provide these fields.

        Parameters
        ----------
        items:
            Flat list of raw review dicts from the actor dataset.  Non-dict
            entries are silently dropped and counted.
        listing:
            Normalized listing; used as the source of ``total_review_count``
            and ``average_rating`` fallbacks.

        Returns
        -------
        ReviewExtractionResult
            Always valid; empty corpus when *items* is empty or all malformed.
        """
        comments: list[UnifiedReviewComment] = []
        dropped = 0
        for item in items:
            parsed = _parse_comment(item)
            if parsed is not None:
                comments.append(parsed)
            else:
                dropped += 1

        # total_review_count: prefer listing metadata (actor does not provide aggregate)
        total_count: int | None
        if listing is not None and getattr(listing, "review_count", None) is not None:
            total_count = listing.review_count
        else:
            total_count = len(comments) if comments else None

        # average_rating: prefer listing metadata
        average_rating: float | None = None
        if listing is not None:
            average_rating = getattr(listing, "rating", None)

        source_id = getattr(listing, "source_id", None) if listing is not None else None
        source_url = getattr(listing, "source_url", None) if listing is not None else None

        corpus = ReviewCorpus(
            source_provider=_SOURCE_PROVIDER,
            source_listing_id=str(source_id) if source_id is not None else None,
            source_url=source_url,
            total_review_count=total_count,
            average_rating=average_rating,
            comments=comments,
        )
        return ReviewExtractionResult(
            corpus=corpus,
            extracted_comment_count=len(comments),
            dropped_comment_count=dropped,
        )

