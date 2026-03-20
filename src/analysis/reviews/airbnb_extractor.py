"""Airbnb raw-payload review extractor.

``AirbnbReviewExtractor`` extracts guest reviews from the raw Apify actor
payload for an Airbnb listing.  It is deliberately defensive: all field
lookups fall back gracefully when a key is absent or holds an unexpected
type, so a sparse or malformed payload produces an empty ``ReviewsData``
rather than raising an exception.

Expected raw payload shape (curious_coder~airbnb-scraper with scrapeReviews=True):

.. code-block:: json

    {
      "reviews": [
        {
          "reviewer": {"firstName": "Alice"},
          "createdAt": "2024-06-01",
          "rating": 5,
          "comments": "Great place!"
        }
      ],
      "reviewsCount": 42,
      "starRating": 4.8
    }

Alternative field names handled:
- Reviews array: ``reviews`` or ``feedbacks``
- Reviewer name: ``reviewer.firstName``, ``reviewer.name``, ``authorName``
- Date: ``createdAt``, ``localizedDate``, ``date``
- Review text: ``comments``, ``text``, ``body``
- Per-review rating: ``rating`` (may be absent)
"""

from __future__ import annotations

from typing import Any

from src.domain.review import Review, ReviewsData


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


def _extract_reviewer_name(item: dict[str, Any]) -> str | None:
    """Return the reviewer display name from an Airbnb review dict."""
    reviewer = item.get("reviewer")
    if isinstance(reviewer, dict):
        name = reviewer.get("firstName") or reviewer.get("name")
        if name:
            return _str_or_none(str(name))
    return _str_or_none(item.get("authorName"))


def _extract_date(item: dict[str, Any]) -> str | None:
    """Return the review date string from an Airbnb review dict."""
    return (
        _str_or_none(item.get("createdAt"))
        or _str_or_none(item.get("localizedDate"))
        or _str_or_none(item.get("date"))
    )


def _extract_text(item: dict[str, Any]) -> str | None:
    """Return the review body text from an Airbnb review dict."""
    return (
        _str_or_none(item.get("comments"))
        or _str_or_none(item.get("text"))
        or _str_or_none(item.get("body"))
    )


def _parse_review(item: Any) -> Review | None:
    """Parse a single review dict.  Returns ``None`` for non-dict inputs."""
    if not isinstance(item, dict):
        return None
    return Review(
        reviewer_name=_extract_reviewer_name(item),
        date=_extract_date(item),
        rating=_float_or_none(item.get("rating")),
        text=_extract_text(item),
    )


class AirbnbReviewExtractor:
    """Extracts guest reviews from an Airbnb raw Apify payload.

    Usage::

        extractor = AirbnbReviewExtractor()
        reviews_data = extractor.extract(raw_payload, listing)
    """

    def extract(
        self,
        payload: dict[str, Any],
        listing: Any,  # NormalizedListing — kept as Any to avoid circular import
    ) -> ReviewsData:
        """Extract reviews from *payload*.

        Parameters
        ----------
        payload:
            Raw Apify actor item dict (the ``payload`` field of ``RawPayload``).
        listing:
            Normalized listing; used to fall back on listing-level metadata
            for ``total_count`` and ``average_rating`` when the raw payload
            omits them.

        Returns
        -------
        ReviewsData
            Always returns a valid ``ReviewsData``; empty when no review data
            is present in the payload.
        """
        # --- reviews list -------------------------------------------------------
        raw_reviews = payload.get("reviews") or payload.get("feedbacks")
        reviews: list[Review] = []
        if isinstance(raw_reviews, list):
            for item in raw_reviews:
                parsed = _parse_review(item)
                if parsed is not None:
                    reviews.append(parsed)

        # --- total_count --------------------------------------------------------
        # Use explicit None check so a zero value (newly listed) is preserved.
        _rc1 = payload.get("reviewsCount")
        _rc2 = payload.get("reviewCount")
        raw_count = _rc1 if _rc1 is not None else _rc2
        if raw_count is not None:
            try:
                total_count = int(raw_count)
            except (TypeError, ValueError):
                total_count = len(reviews)
        elif listing is not None and getattr(listing, "review_count", None) is not None:
            total_count = listing.review_count  # type: ignore[assignment]
        else:
            total_count = len(reviews)

        # --- average_rating -----------------------------------------------------
        raw_rating = payload.get("starRating") or payload.get("rating")
        average_rating = _float_or_none(raw_rating)
        if average_rating is None and listing is not None:
            average_rating = getattr(listing, "rating", None)

        return ReviewsData(
            reviews=reviews,
            total_count=total_count,
            average_rating=average_rating,
        )
