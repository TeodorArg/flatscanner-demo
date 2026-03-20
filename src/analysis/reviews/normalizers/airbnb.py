"""Airbnb review normalizer.

``AirbnbReviewNormalizer`` maps a raw Apify actor payload for an Airbnb
listing into the unified ``ReviewCorpus`` contract.  Field extraction is
deliberately defensive: all lookups fall back gracefully when a key is absent
or holds an unexpected type.

Expected raw payload shape (curious_coder~airbnb-scraper with scrapeReviews=True):

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

Alternative field names handled:
- Reviews array: ``reviews`` or ``feedbacks``
- Comment id: ``id`` or ``reviewId``
- Reviewer name: ``reviewer.firstName``, ``reviewer.name``, ``authorName``
- Reviewer origin: ``reviewer.location``, ``reviewer.hometown``
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
        return (
            _str_or_none(reviewer.get("location"))
            or _str_or_none(reviewer.get("hometown"))
        )
    return None


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
    """Normalizes a raw Airbnb Apify payload into a unified ``ReviewCorpus``.

    Usage::

        normalizer = AirbnbReviewNormalizer()
        result = normalizer.normalize(raw_payload, listing)
        corpus = result.corpus
    """

    def normalize(
        self,
        payload: dict[str, Any],
        listing: Any,  # NormalizedListing — kept as Any to avoid circular import
    ) -> ReviewExtractionResult:
        """Normalize *payload* into a ``ReviewExtractionResult``.

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
