"""Tests for unified review corpus models and provider normalizers.

Covers:
- UnifiedReviewComment / ReviewCorpus / ReviewExtractionResult domain models
- AirbnbReviewNormalizer: field mapping, fallbacks, empty/missing data,
  host response extraction, reviewer origin, comment id
- GenericReviewNormalizer: listing metadata mapping, always-empty comments
"""

from __future__ import annotations

import pytest

from src.analysis.reviews.normalizers.airbnb import AirbnbReviewNormalizer
from src.analysis.reviews.normalizers.generic import GenericReviewNormalizer
from src.domain.listing import ListingProvider, NormalizedListing
from src.domain.review_corpus import ReviewCorpus, ReviewExtractionResult, UnifiedReviewComment


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _listing(
    provider: ListingProvider = ListingProvider.AIRBNB,
    rating: float | None = 4.5,
    review_count: int | None = 10,
    source_id: str = "1",
    source_url: str = "https://www.airbnb.com/rooms/1",
) -> NormalizedListing:
    return NormalizedListing(
        provider=provider,
        source_url=source_url,
        source_id=source_id,
        title="Test Listing",
        rating=rating,
        review_count=review_count,
    )


# ---------------------------------------------------------------------------
# Corpus domain models
# ---------------------------------------------------------------------------


class TestUnifiedReviewComment:
    def test_required_field_only(self):
        c = UnifiedReviewComment(source_provider="airbnb")
        assert c.source_provider == "airbnb"
        assert c.comment_text == ""
        assert c.source_comment_id is None
        assert c.review_date is None
        assert c.rating is None

    def test_all_fields(self):
        c = UnifiedReviewComment(
            source_provider="airbnb",
            source_comment_id="abc",
            review_date="2024-06-01",
            stay_start_date="2024-05-28",
            stay_end_date="2024-06-01",
            rating=4.5,
            language="en",
            reviewer_name="Alice",
            reviewer_origin="London",
            comment_text="Great stay!",
            host_response_text="Thanks!",
            listing_title_at_review_time="Cozy flat",
            raw_label="5_stars",
        )
        assert c.reviewer_name == "Alice"
        assert c.reviewer_origin == "London"
        assert c.host_response_text == "Thanks!"
        assert c.rating == pytest.approx(4.5)


class TestReviewCorpus:
    def test_defaults(self):
        corpus = ReviewCorpus(source_provider="airbnb")
        assert corpus.comments == []
        assert corpus.total_review_count is None
        assert corpus.average_rating is None
        assert corpus.source_listing_id is None

    def test_with_comments(self):
        comments = [
            UnifiedReviewComment(source_provider="airbnb", comment_text="Nice."),
            UnifiedReviewComment(source_provider="airbnb", comment_text="Good."),
        ]
        corpus = ReviewCorpus(
            source_provider="airbnb",
            total_review_count=42,
            average_rating=4.8,
            comments=comments,
        )
        assert len(corpus.comments) == 2
        assert corpus.total_review_count == 42
        assert corpus.average_rating == pytest.approx(4.8)


class TestReviewExtractionResult:
    def test_defaults(self):
        corpus = ReviewCorpus(source_provider="airbnb")
        result = ReviewExtractionResult(corpus=corpus, extracted_comment_count=0)
        assert result.dropped_comment_count == 0
        assert result.warnings == []

    def test_with_counts(self):
        corpus = ReviewCorpus(source_provider="airbnb")
        result = ReviewExtractionResult(
            corpus=corpus,
            extracted_comment_count=5,
            dropped_comment_count=2,
            warnings=["malformed item at index 3"],
        )
        assert result.extracted_comment_count == 5
        assert result.dropped_comment_count == 2
        assert len(result.warnings) == 1


# ---------------------------------------------------------------------------
# AirbnbReviewNormalizer
# ---------------------------------------------------------------------------


class TestAirbnbReviewNormalizer:
    def setup_method(self):
        self.normalizer = AirbnbReviewNormalizer()

    def test_returns_review_extraction_result(self):
        result = self.normalizer.normalize({}, _listing())
        assert isinstance(result, ReviewExtractionResult)
        assert isinstance(result.corpus, ReviewCorpus)

    def test_corpus_source_provider_is_airbnb(self):
        result = self.normalizer.normalize({}, _listing())
        assert result.corpus.source_provider == "airbnb"

    def test_extracts_reviews_array(self):
        payload = {
            "reviews": [
                {
                    "reviewer": {"firstName": "Alice"},
                    "createdAt": "2024-01-01",
                    "comments": "Great!",
                    "rating": 5,
                },
                {
                    "reviewer": {"firstName": "Bob"},
                    "comments": "Good stay.",
                },
            ],
            "reviewsCount": 2,
            "starRating": 4.8,
        }
        result = self.normalizer.normalize(payload, _listing())
        corpus = result.corpus
        assert len(corpus.comments) == 2
        assert corpus.comments[0].reviewer_name == "Alice"
        assert corpus.comments[0].review_date == "2024-01-01"
        assert corpus.comments[0].comment_text == "Great!"
        assert corpus.comments[0].rating == pytest.approx(5.0)
        assert corpus.comments[0].source_provider == "airbnb"
        assert corpus.comments[1].reviewer_name == "Bob"
        assert corpus.comments[1].comment_text == "Good stay."

    def test_extracts_feedbacks_fallback(self):
        payload = {"feedbacks": [{"comments": "Lovely place."}]}
        result = self.normalizer.normalize(payload, _listing())
        assert len(result.corpus.comments) == 1
        assert result.corpus.comments[0].comment_text == "Lovely place."

    def test_empty_reviews_produces_empty_corpus(self):
        payload = {"reviews": [], "reviewsCount": 0}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments == []
        assert result.corpus.total_review_count == 0
        assert result.extracted_comment_count == 0

    def test_missing_reviews_key(self):
        result = self.normalizer.normalize({}, _listing())
        assert result.corpus.comments == []

    def test_non_dict_items_dropped(self):
        payload = {"reviews": ["not a dict", None, {"comments": "Valid."}]}
        result = self.normalizer.normalize(payload, _listing())
        assert len(result.corpus.comments) == 1
        assert result.corpus.comments[0].comment_text == "Valid."
        assert result.dropped_comment_count == 2

    def test_total_count_from_payload(self):
        payload = {"reviews": [], "reviewsCount": 55}
        result = self.normalizer.normalize(payload, _listing(review_count=10))
        assert result.corpus.total_review_count == 55

    def test_total_count_falls_back_to_listing(self):
        payload = {"reviews": [{"comments": "Good."}]}
        result = self.normalizer.normalize(payload, _listing(review_count=99))
        assert result.corpus.total_review_count == 99

    def test_total_count_falls_back_to_comment_count(self):
        payload = {"reviews": [{"comments": "A."}, {"comments": "B."}]}
        result = self.normalizer.normalize(payload, _listing(review_count=None))
        assert result.corpus.total_review_count == 2

    def test_average_rating_from_payload(self):
        payload = {"starRating": 4.9}
        result = self.normalizer.normalize(payload, _listing(rating=3.0))
        assert result.corpus.average_rating == pytest.approx(4.9)

    def test_average_rating_falls_back_to_listing(self):
        result = self.normalizer.normalize({}, _listing(rating=4.2))
        assert result.corpus.average_rating == pytest.approx(4.2)

    def test_average_rating_none_when_absent(self):
        result = self.normalizer.normalize({}, _listing(rating=None))
        assert result.corpus.average_rating is None

    def test_reviewer_name_from_reviewer_dict(self):
        payload = {"reviews": [{"reviewer": {"firstName": "Carol"}, "comments": "Nice."}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].reviewer_name == "Carol"

    def test_reviewer_name_from_author_name(self):
        payload = {"reviews": [{"authorName": "Dave", "comments": "Good."}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].reviewer_name == "Dave"

    def test_reviewer_origin_from_location(self):
        payload = {
            "reviews": [{"reviewer": {"firstName": "Eve", "location": "Paris"}, "comments": "Nice."}]
        }
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].reviewer_origin == "Paris"

    def test_reviewer_origin_from_hometown(self):
        payload = {
            "reviews": [{"reviewer": {"firstName": "Frank", "hometown": "Berlin"}, "comments": "Good."}]
        }
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].reviewer_origin == "Berlin"

    def test_reviewer_origin_none_when_absent(self):
        payload = {"reviews": [{"reviewer": {"firstName": "Alice"}, "comments": "OK."}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].reviewer_origin is None

    def test_date_alternatives(self):
        payload = {"reviews": [{"localizedDate": "January 2024", "comments": "Nice."}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].review_date == "January 2024"

    def test_date_from_date_field(self):
        payload = {"reviews": [{"date": "2024-03-15", "comments": "OK."}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].review_date == "2024-03-15"

    def test_text_from_text_field(self):
        payload = {"reviews": [{"text": "Fantastic!"}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].comment_text == "Fantastic!"

    def test_text_from_body_field(self):
        payload = {"reviews": [{"body": "Very nice."}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].comment_text == "Very nice."

    def test_empty_comment_text_when_no_text_field(self):
        payload = {"reviews": [{"reviewer": {"firstName": "Alice"}}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].comment_text == ""

    def test_host_response_from_response_field(self):
        payload = {"reviews": [{"comments": "Good.", "response": "Thank you!"}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].host_response_text == "Thank you!"

    def test_host_response_from_host_reply(self):
        payload = {"reviews": [{"comments": "OK.", "hostReply": "Glad you enjoyed it."}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].host_response_text == "Glad you enjoyed it."

    def test_host_response_none_when_absent(self):
        payload = {"reviews": [{"comments": "Fine."}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].host_response_text is None

    def test_comment_id_from_id_field(self):
        payload = {"reviews": [{"id": "review-42", "comments": "Good."}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].source_comment_id == "review-42"

    def test_comment_id_from_review_id_field(self):
        payload = {"reviews": [{"reviewId": "r-99", "comments": "Good."}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].source_comment_id == "r-99"

    def test_language_from_language_field(self):
        payload = {"reviews": [{"comments": "Gut.", "language": "de"}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].language == "de"

    def test_language_from_language_tag(self):
        payload = {"reviews": [{"comments": "Bien.", "languageTag": "fr"}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].language == "fr"

    def test_source_listing_id_from_listing(self):
        result = self.normalizer.normalize({}, _listing(source_id="rooms-1"))
        assert result.corpus.source_listing_id == "rooms-1"

    def test_source_url_from_listing(self):
        result = self.normalizer.normalize({}, _listing(source_url="https://www.airbnb.com/rooms/1"))
        assert result.corpus.source_url == "https://www.airbnb.com/rooms/1"

    def test_extracted_comment_count_matches(self):
        payload = {"reviews": [{"comments": "A."}, {"comments": "B."}, {"comments": "C."}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.extracted_comment_count == 3

    def test_reviewer_origin_from_localized_reviewer_location(self):
        """localizedReviewerLocation (tri_angle reviews actor top-level field) is handled."""
        payload = {
            "reviews": [
                {"comments": "Nice.", "localizedReviewerLocation": "Tokyo"}
            ]
        }
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].reviewer_origin == "Tokyo"

    def test_reviewer_origin_prefers_reviewer_dict_location(self):
        """reviewer.location takes precedence over localizedReviewerLocation."""
        payload = {
            "reviews": [
                {
                    "comments": "Good.",
                    "reviewer": {"firstName": "Bob", "location": "London"},
                    "localizedReviewerLocation": "Berlin",
                }
            ]
        }
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments[0].reviewer_origin == "London"


# ---------------------------------------------------------------------------
# AirbnbReviewNormalizer — normalize_from_actor_items (tri_angle reviews actor)
# ---------------------------------------------------------------------------


_ACTOR_ITEM = {
    "id": "rv-1",
    "language": "en",
    "text": "Lovely flat, great location.",
    "localizedText": "Lovely flat, great location.",
    "localizedDate": "March 2024",
    "createdAt": "2024-03-15",
    "localizedReviewerLocation": "London",
    "reviewer": {"firstName": "Alice"},
    "reviewee": "Host",
    "rating": 5,
    "response": "Thank you Alice!",
    "reviewHighlight": None,
    "startUrl": "https://www.airbnb.com/rooms/1",
}


class TestAirbnbReviewNormalizerFromActorItems:
    def setup_method(self):
        self.normalizer = AirbnbReviewNormalizer()

    def test_returns_review_extraction_result(self):
        result = self.normalizer.normalize_from_actor_items([_ACTOR_ITEM], _listing())
        assert isinstance(result, ReviewExtractionResult)
        assert isinstance(result.corpus, ReviewCorpus)

    def test_corpus_source_provider_is_airbnb(self):
        result = self.normalizer.normalize_from_actor_items([_ACTOR_ITEM], _listing())
        assert result.corpus.source_provider == "airbnb"

    def test_maps_text_field(self):
        result = self.normalizer.normalize_from_actor_items([_ACTOR_ITEM], _listing())
        assert result.corpus.comments[0].comment_text == "Lovely flat, great location."

    def test_maps_language_field(self):
        result = self.normalizer.normalize_from_actor_items([_ACTOR_ITEM], _listing())
        assert result.corpus.comments[0].language == "en"

    def test_maps_localized_date_field(self):
        # createdAt is preferred over localizedDate
        result = self.normalizer.normalize_from_actor_items([_ACTOR_ITEM], _listing())
        assert result.corpus.comments[0].review_date == "2024-03-15"

    def test_maps_localized_reviewer_location(self):
        result = self.normalizer.normalize_from_actor_items([_ACTOR_ITEM], _listing())
        assert result.corpus.comments[0].reviewer_origin == "London"

    def test_maps_reviewer_first_name(self):
        result = self.normalizer.normalize_from_actor_items([_ACTOR_ITEM], _listing())
        assert result.corpus.comments[0].reviewer_name == "Alice"

    def test_maps_rating(self):
        result = self.normalizer.normalize_from_actor_items([_ACTOR_ITEM], _listing())
        assert result.corpus.comments[0].rating == pytest.approx(5.0)

    def test_maps_response_as_host_response(self):
        result = self.normalizer.normalize_from_actor_items([_ACTOR_ITEM], _listing())
        assert result.corpus.comments[0].host_response_text == "Thank you Alice!"

    def test_maps_id_field(self):
        result = self.normalizer.normalize_from_actor_items([_ACTOR_ITEM], _listing())
        assert result.corpus.comments[0].source_comment_id == "rv-1"

    def test_empty_items_list(self):
        result = self.normalizer.normalize_from_actor_items([], _listing())
        assert result.corpus.comments == []
        assert result.extracted_comment_count == 0

    def test_non_dict_items_dropped(self):
        result = self.normalizer.normalize_from_actor_items(
            ["not a dict", None, _ACTOR_ITEM], _listing()
        )
        assert len(result.corpus.comments) == 1
        assert result.dropped_comment_count == 2

    def test_multiple_items_all_normalized(self):
        item2 = dict(_ACTOR_ITEM, id="rv-2", text="Good stay.", reviewer={"firstName": "Bob"})
        result = self.normalizer.normalize_from_actor_items([_ACTOR_ITEM, item2], _listing())
        assert result.extracted_comment_count == 2
        assert result.corpus.comments[1].reviewer_name == "Bob"

    def test_total_count_from_listing_review_count(self):
        result = self.normalizer.normalize_from_actor_items([_ACTOR_ITEM], _listing(review_count=42))
        assert result.corpus.total_review_count == 42

    def test_total_count_falls_back_to_comment_count_when_listing_none(self):
        result = self.normalizer.normalize_from_actor_items([_ACTOR_ITEM], _listing(review_count=None))
        assert result.corpus.total_review_count == 1

    def test_total_count_none_when_empty_and_no_listing_count(self):
        result = self.normalizer.normalize_from_actor_items([], _listing(review_count=None))
        assert result.corpus.total_review_count is None

    def test_average_rating_from_listing(self):
        result = self.normalizer.normalize_from_actor_items([_ACTOR_ITEM], _listing(rating=4.7))
        assert result.corpus.average_rating == pytest.approx(4.7)

    def test_average_rating_none_when_listing_rating_none(self):
        result = self.normalizer.normalize_from_actor_items([_ACTOR_ITEM], _listing(rating=None))
        assert result.corpus.average_rating is None

    def test_source_listing_id_from_listing(self):
        result = self.normalizer.normalize_from_actor_items([], _listing(source_id="rooms-99"))
        assert result.corpus.source_listing_id == "rooms-99"

    def test_source_url_from_listing(self):
        result = self.normalizer.normalize_from_actor_items(
            [], _listing(source_url="https://www.airbnb.com/rooms/99")
        )
        assert result.corpus.source_url == "https://www.airbnb.com/rooms/99"

    def test_localized_date_used_when_created_at_absent(self):
        item = {
            "id": "rv-3",
            "text": "Nice!",
            "localizedDate": "January 2024",
            "reviewer": {"firstName": "Carol"},
            "rating": 4,
        }
        result = self.normalizer.normalize_from_actor_items([item], _listing())
        assert result.corpus.comments[0].review_date == "January 2024"

    def test_no_response_maps_to_none(self):
        item = dict(_ACTOR_ITEM, response=None)
        result = self.normalizer.normalize_from_actor_items([item], _listing())
        assert result.corpus.comments[0].host_response_text is None


# ---------------------------------------------------------------------------
# GenericReviewNormalizer
# ---------------------------------------------------------------------------


class TestGenericReviewNormalizer:
    def setup_method(self):
        self.normalizer = GenericReviewNormalizer()

    def test_returns_review_extraction_result(self):
        result = self.normalizer.normalize({}, _listing())
        assert isinstance(result, ReviewExtractionResult)

    def test_comments_always_empty(self):
        # Payload with reviews should be ignored
        payload = {"reviews": [{"comments": "Ignored."}]}
        result = self.normalizer.normalize(payload, _listing())
        assert result.corpus.comments == []

    def test_extracted_comment_count_always_zero(self):
        result = self.normalizer.normalize({}, _listing())
        assert result.extracted_comment_count == 0

    def test_total_count_from_listing(self):
        result = self.normalizer.normalize({}, _listing(review_count=77))
        assert result.corpus.total_review_count == 77

    def test_total_count_none_when_listing_review_count_none(self):
        result = self.normalizer.normalize({}, _listing(review_count=None))
        assert result.corpus.total_review_count is None

    def test_average_rating_from_listing(self):
        result = self.normalizer.normalize({}, _listing(rating=4.3))
        assert result.corpus.average_rating == pytest.approx(4.3)

    def test_average_rating_none_when_absent(self):
        result = self.normalizer.normalize({}, _listing(rating=None))
        assert result.corpus.average_rating is None

    def test_source_provider_from_listing_provider(self):
        result = self.normalizer.normalize({}, _listing(provider=ListingProvider.AIRBNB))
        assert result.corpus.source_provider == "airbnb"

    def test_source_listing_id_from_listing(self):
        result = self.normalizer.normalize({}, _listing(source_id="abc"))
        assert result.corpus.source_listing_id == "abc"

    def test_source_url_from_listing(self):
        result = self.normalizer.normalize({}, _listing(source_url="https://example.com/listing"))
        assert result.corpus.source_url == "https://example.com/listing"
