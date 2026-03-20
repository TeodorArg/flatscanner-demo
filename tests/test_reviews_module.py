"""Tests for the P4 reviews analysis module.

Covers:
- Review / ReviewsData domain models
- AirbnbReviewExtractor: field mapping, fallbacks, empty/missing data
- GenericReviewExtractor: listing metadata mapping
- build_reviews_prompt: content and structure
- parse_reviews_response: valid JSON, code fences, missing fields, invalid input
- ReviewAnalysisService: delegates to OpenRouter, propagates errors
- AirbnbReviewsModule: name/providers contract, run() with and without raw payload,
  AI call skipped when no review texts
- GenericReviewsModule: name/providers contract, run() metadata-only result
- End-to-end roundtrip through registry + runner
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.analysis.context import AnalysisContext
from src.analysis.module import AnalysisModule
from src.analysis.modules.reviews import (
    AirbnbReviewsModule,
    GenericReviewsModule,
    ReviewsResult,
)
from src.analysis.registry import ModuleRegistry
from src.analysis.reviews.airbnb_extractor import AirbnbReviewExtractor
from src.analysis.reviews.extractor import ReviewAnalysisOutput
from src.analysis.reviews.generic_extractor import GenericReviewExtractor
from src.analysis.reviews.service import (
    ReviewAnalysisService,
    build_reviews_prompt,
    parse_reviews_response,
)
from src.domain.listing import ListingProvider, NormalizedListing
from src.domain.raw_payload import RawPayload
from src.domain.review import Review, ReviewsData


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _listing(
    provider: ListingProvider = ListingProvider.AIRBNB,
    rating: float | None = 4.5,
    review_count: int | None = 10,
) -> NormalizedListing:
    return NormalizedListing(
        provider=provider,
        source_url="https://www.airbnb.com/rooms/1",
        source_id="1",
        title="Test Listing",
        rating=rating,
        review_count=review_count,
    )


def _raw_payload(payload: dict) -> RawPayload:
    return RawPayload(
        provider="airbnb",
        source_url="https://www.airbnb.com/rooms/1",
        source_id="1",
        payload=payload,
    )


def _make_review_service(output: ReviewAnalysisOutput | None = None) -> ReviewAnalysisService:
    svc = MagicMock(spec=ReviewAnalysisService)
    svc.analyse = AsyncMock(
        return_value=output
        or ReviewAnalysisOutput(
            sentiment_summary="Guests love it.",
            common_themes=["Clean", "Location"],
            concerns=["Noise"],
        )
    )
    return svc


# ---------------------------------------------------------------------------
# Review domain models
# ---------------------------------------------------------------------------


class TestReviewDomainModels:
    def test_review_all_fields(self):
        r = Review(reviewer_name="Alice", date="2024-01-01", rating=5.0, text="Great!")
        assert r.reviewer_name == "Alice"
        assert r.date == "2024-01-01"
        assert r.rating == 5.0
        assert r.text == "Great!"

    def test_review_defaults_all_none(self):
        r = Review()
        assert r.reviewer_name is None
        assert r.date is None
        assert r.rating is None
        assert r.text is None

    def test_reviews_data_defaults(self):
        rd = ReviewsData()
        assert rd.reviews == []
        assert rd.total_count == 0
        assert rd.average_rating is None

    def test_reviews_data_with_values(self):
        reviews = [Review(text="Nice"), Review(text="Okay")]
        rd = ReviewsData(reviews=reviews, total_count=42, average_rating=4.7)
        assert len(rd.reviews) == 2
        assert rd.total_count == 42
        assert rd.average_rating == pytest.approx(4.7)


# ---------------------------------------------------------------------------
# AirbnbReviewExtractor
# ---------------------------------------------------------------------------


class TestAirbnbReviewExtractor:
    def setup_method(self):
        self.extractor = AirbnbReviewExtractor()

    def test_extracts_reviews_array(self):
        payload = {
            "reviews": [
                {"reviewer": {"firstName": "Alice"}, "createdAt": "2024-01-01", "comments": "Great!", "rating": 5},
                {"reviewer": {"firstName": "Bob"}, "comments": "Good stay."},
            ],
            "reviewsCount": 2,
            "starRating": 4.8,
        }
        rd = self.extractor.extract(payload, _listing())
        assert len(rd.reviews) == 2
        assert rd.reviews[0].reviewer_name == "Alice"
        assert rd.reviews[0].date == "2024-01-01"
        assert rd.reviews[0].text == "Great!"
        assert rd.reviews[0].rating == pytest.approx(5.0)
        assert rd.reviews[1].reviewer_name == "Bob"
        assert rd.reviews[1].text == "Good stay."

    def test_extracts_feedbacks_fallback(self):
        payload = {
            "feedbacks": [{"comments": "Lovely place."}],
        }
        rd = self.extractor.extract(payload, _listing())
        assert len(rd.reviews) == 1
        assert rd.reviews[0].text == "Lovely place."

    def test_empty_reviews_array(self):
        payload = {"reviews": [], "reviewsCount": 0}
        rd = self.extractor.extract(payload, _listing())
        assert rd.reviews == []
        assert rd.total_count == 0

    def test_missing_reviews_key(self):
        rd = self.extractor.extract({}, _listing())
        assert rd.reviews == []

    def test_total_count_from_payload(self):
        payload = {"reviews": [], "reviewsCount": 55}
        rd = self.extractor.extract(payload, _listing(review_count=10))
        assert rd.total_count == 55

    def test_total_count_falls_back_to_listing(self):
        payload = {"reviews": [{"comments": "Good."}]}
        rd = self.extractor.extract(payload, _listing(review_count=99))
        # reviewsCount absent → falls back to listing.review_count
        assert rd.total_count == 99

    def test_total_count_falls_back_to_len_reviews(self):
        payload = {"reviews": [{"comments": "A."}, {"comments": "B."}]}
        rd = self.extractor.extract(payload, _listing(review_count=None))
        assert rd.total_count == 2

    def test_average_rating_from_payload(self):
        payload = {"starRating": 4.9}
        rd = self.extractor.extract(payload, _listing(rating=3.0))
        assert rd.average_rating == pytest.approx(4.9)

    def test_average_rating_falls_back_to_listing(self):
        rd = self.extractor.extract({}, _listing(rating=4.2))
        assert rd.average_rating == pytest.approx(4.2)

    def test_average_rating_none_when_absent(self):
        rd = self.extractor.extract({}, _listing(rating=None))
        assert rd.average_rating is None

    def test_reviewer_name_from_reviewer_dict(self):
        payload = {"reviews": [{"reviewer": {"firstName": "Carol"}, "comments": "Nice."}]}
        rd = self.extractor.extract(payload, _listing())
        assert rd.reviews[0].reviewer_name == "Carol"

    def test_reviewer_name_from_author_name(self):
        payload = {"reviews": [{"authorName": "Dave", "comments": "Good."}]}
        rd = self.extractor.extract(payload, _listing())
        assert rd.reviews[0].reviewer_name == "Dave"

    def test_date_alternatives(self):
        payload = {"reviews": [{"localizedDate": "January 2024", "comments": "Nice."}]}
        rd = self.extractor.extract(payload, _listing())
        assert rd.reviews[0].date == "January 2024"

    def test_text_alternatives(self):
        payload = {"reviews": [{"body": "Fantastic!"}]}
        rd = self.extractor.extract(payload, _listing())
        assert rd.reviews[0].text == "Fantastic!"

    def test_non_dict_items_skipped(self):
        payload = {"reviews": ["not a dict", None, {"comments": "Valid."}]}
        rd = self.extractor.extract(payload, _listing())
        assert len(rd.reviews) == 1
        assert rd.reviews[0].text == "Valid."


# ---------------------------------------------------------------------------
# GenericReviewExtractor
# ---------------------------------------------------------------------------


class TestGenericReviewExtractor:
    def setup_method(self):
        self.extractor = GenericReviewExtractor()

    def test_empty_reviews_list(self):
        rd = self.extractor.extract({}, _listing())
        assert rd.reviews == []

    def test_total_count_from_listing(self):
        rd = self.extractor.extract({}, _listing(review_count=77))
        assert rd.total_count == 77

    def test_total_count_zero_when_none(self):
        rd = self.extractor.extract({}, _listing(review_count=None))
        assert rd.total_count == 0

    def test_average_rating_from_listing(self):
        rd = self.extractor.extract({}, _listing(rating=4.3))
        assert rd.average_rating == pytest.approx(4.3)

    def test_average_rating_none_when_absent(self):
        rd = self.extractor.extract({}, _listing(rating=None))
        assert rd.average_rating is None

    def test_payload_ignored(self):
        # payload parameter is ignored by the generic extractor
        rd = self.extractor.extract({"reviews": [{"comments": "Irrelevant"}]}, _listing(review_count=5))
        assert rd.reviews == []
        assert rd.total_count == 5


# ---------------------------------------------------------------------------
# build_reviews_prompt
# ---------------------------------------------------------------------------


class TestBuildReviewsPrompt:
    def test_includes_total_count(self):
        rd = ReviewsData(total_count=20, average_rating=4.5)
        prompt = build_reviews_prompt(rd)
        assert "Total reviews: 20" in prompt

    def test_includes_average_rating(self):
        rd = ReviewsData(average_rating=4.75)
        prompt = build_reviews_prompt(rd)
        assert "4.75" in prompt

    def test_omits_rating_when_none(self):
        rd = ReviewsData(average_rating=None)
        prompt = build_reviews_prompt(rd)
        assert "Average rating" not in prompt

    def test_includes_sample_review_texts(self):
        rd = ReviewsData(
            reviews=[Review(text="Brilliant stay!"), Review(text="Would revisit.")],
            total_count=2,
        )
        prompt = build_reviews_prompt(rd)
        assert "Brilliant stay!" in prompt
        assert "Would revisit." in prompt

    def test_skips_reviews_without_text(self):
        rd = ReviewsData(reviews=[Review(text=None), Review(text="")], total_count=2)
        prompt = build_reviews_prompt(rd)
        assert "Sample reviews" not in prompt

    def test_truncates_long_review_text(self):
        long_text = "A" * 400
        rd = ReviewsData(reviews=[Review(text=long_text)])
        prompt = build_reviews_prompt(rd)
        assert "A" * 300 in prompt
        assert "..." in prompt

    def test_caps_at_ten_reviews(self):
        rd = ReviewsData(
            reviews=[Review(text=f"Review {i}") for i in range(15)],
        )
        prompt = build_reviews_prompt(rd)
        # Only reviews 0-9 should appear
        assert "Review 9" in prompt
        assert "Review 10" not in prompt

    def test_includes_json_schema_hint(self):
        rd = ReviewsData()
        prompt = build_reviews_prompt(rd)
        assert "sentiment_summary" in prompt
        assert "common_themes" in prompt
        assert "concerns" in prompt


# ---------------------------------------------------------------------------
# parse_reviews_response
# ---------------------------------------------------------------------------


class TestParseReviewsResponse:
    def test_valid_json(self):
        raw = '{"sentiment_summary": "Great!", "common_themes": ["Clean"], "concerns": ["Noisy"]}'
        out = parse_reviews_response(raw)
        assert out.sentiment_summary == "Great!"
        assert out.common_themes == ["Clean"]
        assert out.concerns == ["Noisy"]

    def test_strips_code_fences(self):
        raw = '```json\n{"sentiment_summary": "Good.", "common_themes": [], "concerns": []}\n```'
        out = parse_reviews_response(raw)
        assert out.sentiment_summary == "Good."

    def test_missing_fields_use_defaults(self):
        raw = '{"sentiment_summary": "Fine."}'
        out = parse_reviews_response(raw)
        assert out.common_themes == []
        assert out.concerns == []

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="not valid JSON"):
            parse_reviews_response("not json")

    def test_non_object_raises(self):
        with pytest.raises(ValueError, match="JSON object"):
            parse_reviews_response("[1, 2, 3]")

    def test_invalid_list_fields_default_to_empty(self):
        raw = '{"sentiment_summary": "OK.", "common_themes": "string not list", "concerns": 42}'
        out = parse_reviews_response(raw)
        assert out.common_themes == []
        assert out.concerns == []

    def test_non_string_sentiment_defaults_to_empty(self):
        raw = '{"sentiment_summary": 123}'
        out = parse_reviews_response(raw)
        assert out.sentiment_summary == ""


# ---------------------------------------------------------------------------
# ReviewAnalysisService
# ---------------------------------------------------------------------------


class TestReviewAnalysisService:
    @pytest.mark.asyncio
    async def test_calls_openrouter_and_returns_output(self):
        from src.analysis.openrouter_client import OpenRouterClient

        mock_client = MagicMock(spec=OpenRouterClient)
        mock_client.chat = AsyncMock(
            return_value='{"sentiment_summary": "Lovely.", "common_themes": ["Quiet"], "concerns": []}'
        )
        settings = MagicMock()
        svc = ReviewAnalysisService(settings=settings, client=mock_client)
        rd = ReviewsData(
            reviews=[Review(text="Very nice place!")],
            total_count=1,
            average_rating=5.0,
        )
        out = await svc.analyse(rd)
        assert out.sentiment_summary == "Lovely."
        assert out.common_themes == ["Quiet"]
        mock_client.chat.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_prompt_sent_as_user_message(self):
        from src.analysis.openrouter_client import OpenRouterClient

        mock_client = MagicMock(spec=OpenRouterClient)
        mock_client.chat = AsyncMock(
            return_value='{"sentiment_summary": "OK.", "common_themes": [], "concerns": []}'
        )
        settings = MagicMock()
        svc = ReviewAnalysisService(settings=settings, client=mock_client)
        rd = ReviewsData(reviews=[Review(text="Fine.")], total_count=1)
        await svc.analyse(rd)
        messages = mock_client.chat.call_args[0][0]
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Fine." in messages[1]["content"]

    @pytest.mark.asyncio
    async def test_propagates_openrouter_error(self):
        from src.analysis.openrouter_client import OpenRouterClient, OpenRouterError

        mock_client = MagicMock(spec=OpenRouterClient)
        mock_client.chat = AsyncMock(side_effect=OpenRouterError("API down"))
        settings = MagicMock()
        svc = ReviewAnalysisService(settings=settings, client=mock_client)
        rd = ReviewsData(reviews=[Review(text="Test.")])
        with pytest.raises(OpenRouterError, match="API down"):
            await svc.analyse(rd)

    @pytest.mark.asyncio
    async def test_propagates_parse_error(self):
        from src.analysis.openrouter_client import OpenRouterClient

        mock_client = MagicMock(spec=OpenRouterClient)
        mock_client.chat = AsyncMock(return_value="not json at all")
        settings = MagicMock()
        svc = ReviewAnalysisService(settings=settings, client=mock_client)
        rd = ReviewsData(reviews=[Review(text="Test.")])
        with pytest.raises(ValueError):
            await svc.analyse(rd)


# ---------------------------------------------------------------------------
# AirbnbReviewsModule
# ---------------------------------------------------------------------------


class TestAirbnbReviewsModule:
    def test_name_is_reviews(self):
        mod = AirbnbReviewsModule(service=_make_review_service())
        assert mod.name == "reviews"

    def test_supported_providers_is_airbnb_only(self):
        mod = AirbnbReviewsModule(service=_make_review_service())
        assert mod.supported_providers == frozenset({ListingProvider.AIRBNB})

    def test_satisfies_module_protocol(self):
        mod = AirbnbReviewsModule(service=_make_review_service())
        assert isinstance(mod, AnalysisModule)

    @pytest.mark.asyncio
    async def test_run_with_raw_payload_and_reviews_calls_ai(self):
        svc = _make_review_service()
        mod = AirbnbReviewsModule(service=svc)
        payload = {"reviews": [{"comments": "Excellent!"}], "reviewsCount": 1, "starRating": 5.0}
        ctx = AnalysisContext(
            listing=_listing(),
            raw_payload=_raw_payload(payload),
        )
        result = await mod.run(ctx)
        assert isinstance(result, ReviewsResult)
        assert result.module_name == "reviews"
        assert result.sentiment_summary == "Guests love it."
        assert result.common_themes == ["Clean", "Location"]
        svc.analyse.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_without_raw_payload_falls_back_to_generic(self):
        svc = _make_review_service()
        mod = AirbnbReviewsModule(service=svc)
        ctx = AnalysisContext(listing=_listing(review_count=5, rating=4.0))
        result = await mod.run(ctx)
        # No review texts → no AI call
        svc.analyse.assert_not_awaited()
        assert result.review_count == 5
        assert result.average_rating == pytest.approx(4.0)

    @pytest.mark.asyncio
    async def test_run_skips_ai_when_no_review_texts(self):
        svc = _make_review_service()
        mod = AirbnbReviewsModule(service=svc)
        # raw_payload with empty reviews list
        payload = {"reviews": [], "reviewsCount": 0}
        ctx = AnalysisContext(
            listing=_listing(),
            raw_payload=_raw_payload(payload),
        )
        result = await mod.run(ctx)
        svc.analyse.assert_not_awaited()
        assert result.sentiment_summary is None

    @pytest.mark.asyncio
    async def test_run_returns_review_count_from_payload(self):
        svc = _make_review_service()
        mod = AirbnbReviewsModule(service=svc)
        payload = {"reviews": [{"comments": "Nice."}], "reviewsCount": 42}
        ctx = AnalysisContext(
            listing=_listing(),
            raw_payload=_raw_payload(payload),
        )
        result = await mod.run(ctx)
        assert result.review_count == 42


# ---------------------------------------------------------------------------
# GenericReviewsModule
# ---------------------------------------------------------------------------


class TestGenericReviewsModule:
    def test_name_is_reviews(self):
        mod = GenericReviewsModule()
        assert mod.name == "reviews"

    def test_supported_providers_is_empty(self):
        mod = GenericReviewsModule()
        assert mod.supported_providers == frozenset()

    def test_satisfies_module_protocol(self):
        mod = GenericReviewsModule()
        assert isinstance(mod, AnalysisModule)

    @pytest.mark.asyncio
    async def test_run_returns_metadata_only(self):
        mod = GenericReviewsModule()
        ctx = AnalysisContext(listing=_listing(review_count=20, rating=4.2))
        result = await mod.run(ctx)
        assert isinstance(result, ReviewsResult)
        assert result.module_name == "reviews"
        assert result.review_count == 20
        assert result.average_rating == pytest.approx(4.2)
        assert result.sentiment_summary is None
        assert result.common_themes == []
        assert result.concerns == []

    @pytest.mark.asyncio
    async def test_run_with_none_listing_metadata(self):
        mod = GenericReviewsModule()
        ctx = AnalysisContext(listing=_listing(review_count=None, rating=None))
        result = await mod.run(ctx)
        assert result.review_count is None
        assert result.average_rating is None


# ---------------------------------------------------------------------------
# End-to-end roundtrip through registry + runner
# ---------------------------------------------------------------------------


class TestReviewsModuleRoundtrip:
    @pytest.mark.asyncio
    async def test_airbnb_module_resolved_for_airbnb_listing(self):
        svc = _make_review_service()
        airbnb_mod = AirbnbReviewsModule(service=svc)
        generic_mod = GenericReviewsModule()

        registry = ModuleRegistry()
        registry.register(airbnb_mod)
        registry.register(generic_mod)

        resolved = registry.resolve("reviews", ListingProvider.AIRBNB)
        assert resolved is airbnb_mod

    @pytest.mark.asyncio
    async def test_generic_module_resolved_for_unknown_provider(self):
        svc = _make_review_service()
        airbnb_mod = AirbnbReviewsModule(service=svc)
        generic_mod = GenericReviewsModule()

        registry = ModuleRegistry()
        registry.register(airbnb_mod)
        registry.register(generic_mod)

        resolved = registry.resolve("reviews", ListingProvider.UNKNOWN)
        assert resolved is generic_mod

    @pytest.mark.asyncio
    async def test_runner_returns_reviews_result(self):
        from src.analysis.runner import ModuleRunner

        svc = _make_review_service()
        mod = GenericReviewsModule()

        registry = ModuleRegistry()
        registry.register(mod)
        runner = ModuleRunner(registry)

        ctx = AnalysisContext(listing=_listing(review_count=5, rating=4.0))
        results = await runner.run(ctx)
        assert len(results) == 1
        assert isinstance(results[0], ReviewsResult)
        assert results[0].module_name == "reviews"


# ---------------------------------------------------------------------------
# AirbnbReviewsModule — non-blocking degradation on AI failure
# ---------------------------------------------------------------------------


class TestAirbnbReviewsModuleDegradation:
    """AirbnbReviewsModule must degrade to metadata-only when AI analysis fails."""

    @pytest.mark.asyncio
    async def test_degrades_on_openrouter_error(self):
        """OpenRouterError from analyse() → metadata-only ReviewsResult, no re-raise."""
        from src.analysis.openrouter_client import OpenRouterError

        svc = MagicMock(spec=ReviewAnalysisService)
        svc.analyse = AsyncMock(side_effect=OpenRouterError("API down"))
        mod = AirbnbReviewsModule(service=svc)

        payload = {"reviews": [{"comments": "Great!"}], "reviewsCount": 5, "starRating": 4.5}
        ctx = AnalysisContext(listing=_listing(), raw_payload=_raw_payload(payload))

        result = await mod.run(ctx)

        assert isinstance(result, ReviewsResult)
        assert result.module_name == "reviews"
        # AI fields absent — degraded to metadata-only
        assert result.sentiment_summary is None
        assert result.common_themes == []
        assert result.concerns == []
        # Metadata from payload still present
        assert result.review_count == 5
        assert result.average_rating == pytest.approx(4.5)

    @pytest.mark.asyncio
    async def test_degrades_on_parse_error(self):
        """ValueError from analyse() (bad JSON) → metadata-only ReviewsResult."""
        svc = MagicMock(spec=ReviewAnalysisService)
        svc.analyse = AsyncMock(side_effect=ValueError("not valid JSON"))
        mod = AirbnbReviewsModule(service=svc)

        payload = {"reviews": [{"comments": "Nice spot."}], "reviewsCount": 3}
        ctx = AnalysisContext(listing=_listing(review_count=3, rating=4.0), raw_payload=_raw_payload(payload))

        result = await mod.run(ctx)

        assert isinstance(result, ReviewsResult)
        assert result.sentiment_summary is None
        assert result.common_themes == []

    @pytest.mark.asyncio
    async def test_job_not_blocked_when_reviews_fail(self):
        """ModuleRunner propagates a ReviewsResult even when AI raises."""
        from src.analysis.openrouter_client import OpenRouterError
        from src.analysis.runner import ModuleRunner

        svc = MagicMock(spec=ReviewAnalysisService)
        svc.analyse = AsyncMock(side_effect=OpenRouterError("down"))
        mod = AirbnbReviewsModule(service=svc)

        registry = ModuleRegistry()
        registry.register(mod)
        runner = ModuleRunner(registry)

        payload = {"reviews": [{"comments": "Loved it."}], "reviewsCount": 1}
        ctx = AnalysisContext(listing=_listing(), raw_payload=_raw_payload(payload))

        results = await runner.run(ctx)
        assert len(results) == 1
        assert isinstance(results[0], ReviewsResult)
        assert results[0].sentiment_summary is None
