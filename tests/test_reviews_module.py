"""Tests for the reviews analysis module (P4 baseline + P023 updates).

Covers:
- Review / ReviewsData legacy domain models (unchanged)
- AirbnbReviewExtractor: field mapping, fallbacks, empty/missing data (unchanged)
- GenericReviewExtractor: listing metadata mapping (unchanged)
- build_reviews_prompt: accepts ReviewCorpus, content and structure
- parse_reviews_response: incident-oriented schema, code fences, missing fields, invalid input
- ReviewAnalysisService: delegates to OpenRouter with ReviewCorpus, propagates errors
- AirbnbReviewsModule: name/providers contract, run() with and without raw payload,
  AI call skipped when no comment texts, incident-oriented output fields
- GenericReviewsModule: name/providers contract, run() metadata-only result
- End-to-end roundtrip through registry + runner
- AirbnbReviewsModule non-blocking degradation on AI failure
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

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
from src.domain.review_corpus import ReviewCorpus, UnifiedReviewComment


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


def _make_corpus(
    comments: list[UnifiedReviewComment] | None = None,
    total_review_count: int = 5,
    average_rating: float | None = 4.5,
) -> ReviewCorpus:
    return ReviewCorpus(
        source_provider="airbnb",
        total_review_count=total_review_count,
        average_rating=average_rating,
        comments=comments or [],
    )


def _make_review_service(output: ReviewAnalysisOutput | None = None) -> ReviewAnalysisService:
    svc = MagicMock(spec=ReviewAnalysisService)
    svc.analyse = AsyncMock(
        return_value=output
        or ReviewAnalysisOutput(
            overall_assessment="Generally positive stay.",
            overall_risk_level="low",
            confidence="medium",
            incident_timeline=[],
            recurring_issues=[],
            conflicts_or_disputes=[],
            critical_red_flags=[],
            positive_signals=["Clean", "Good location"],
            window_view_summary="City view mentioned by several guests.",
        )
    )
    return svc


# ---------------------------------------------------------------------------
# Review legacy domain models (unchanged)
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
# AirbnbReviewExtractor (legacy — still present for backward compat)
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
# GenericReviewExtractor (legacy — still present for backward compat)
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
        rd = self.extractor.extract({"reviews": [{"comments": "Irrelevant"}]}, _listing(review_count=5))
        assert rd.reviews == []
        assert rd.total_count == 5


# ---------------------------------------------------------------------------
# build_reviews_prompt (now accepts ReviewCorpus)
# ---------------------------------------------------------------------------


class TestBuildReviewsPrompt:
    def test_includes_total_count(self):
        corpus = _make_corpus(total_review_count=20)
        prompt = build_reviews_prompt(corpus)
        assert "Total reviews: 20" in prompt

    def test_includes_average_rating(self):
        corpus = _make_corpus(average_rating=4.75)
        prompt = build_reviews_prompt(corpus)
        assert "4.75" in prompt

    def test_omits_rating_when_none(self):
        corpus = _make_corpus(average_rating=None)
        prompt = build_reviews_prompt(corpus)
        assert "Average rating" not in prompt

    def test_includes_sample_comment_texts(self):
        comments = [
            UnifiedReviewComment(source_provider="airbnb", comment_text="Brilliant stay!"),
            UnifiedReviewComment(source_provider="airbnb", comment_text="Would revisit."),
        ]
        corpus = _make_corpus(comments=comments, total_review_count=2)
        prompt = build_reviews_prompt(corpus)
        assert "Brilliant stay!" in prompt
        assert "Would revisit." in prompt

    def test_skips_comments_without_text(self):
        comments = [UnifiedReviewComment(source_provider="airbnb", comment_text="")]
        corpus = _make_corpus(comments=comments)
        prompt = build_reviews_prompt(corpus)
        assert "Sample reviews" not in prompt

    def test_truncates_long_comment_text(self):
        long_text = "A" * 500
        comments = [UnifiedReviewComment(source_provider="airbnb", comment_text=long_text)]
        corpus = _make_corpus(comments=comments)
        prompt = build_reviews_prompt(corpus)
        assert "A" * 400 in prompt
        assert "..." in prompt

    def test_caps_at_twenty_reviews(self):
        comments = [
            UnifiedReviewComment(source_provider="airbnb", comment_text=f"Review {i}")
            for i in range(25)
        ]
        corpus = _make_corpus(comments=comments)
        prompt = build_reviews_prompt(corpus)
        assert "Review 19" in prompt
        assert "Review 20" not in prompt

    def test_includes_incident_oriented_schema_fields(self):
        corpus = _make_corpus()
        prompt = build_reviews_prompt(corpus)
        assert "overall_assessment" in prompt
        assert "incident_timeline" in prompt
        assert "overall_risk_level" in prompt
        assert "window_view_summary" in prompt

    def test_includes_comment_date_in_prompt(self):
        comments = [
            UnifiedReviewComment(
                source_provider="airbnb",
                comment_text="Great!",
                review_date="2024-06-01",
            )
        ]
        corpus = _make_corpus(comments=comments)
        prompt = build_reviews_prompt(corpus)
        assert "2024-06-01" in prompt

    def test_includes_host_response_in_prompt(self):
        comments = [
            UnifiedReviewComment(
                source_provider="airbnb",
                comment_text="Some issues.",
                host_response_text="Sorry to hear that!",
            )
        ]
        corpus = _make_corpus(comments=comments)
        prompt = build_reviews_prompt(corpus)
        assert "Host response" in prompt
        assert "Sorry to hear that!" in prompt


# ---------------------------------------------------------------------------
# parse_reviews_response (incident-oriented schema)
# ---------------------------------------------------------------------------


class TestParseReviewsResponse:
    def _valid_json(self, **overrides) -> str:
        import json
        base = {
            "overall_assessment": "Generally positive.",
            "overall_risk_level": "low",
            "confidence": "medium",
            "incident_timeline": [],
            "recurring_issues": [],
            "conflicts_or_disputes": [],
            "critical_red_flags": [],
            "positive_signals": ["Clean"],
            "window_view_summary": "City view.",
        }
        base.update(overrides)
        return json.dumps(base)

    def test_valid_json_all_fields(self):
        raw = self._valid_json()
        out = parse_reviews_response(raw)
        assert out.overall_assessment == "Generally positive."
        assert out.overall_risk_level == "low"
        assert out.confidence == "medium"
        assert out.positive_signals == ["Clean"]
        assert out.window_view_summary == "City view."

    def test_incident_timeline_parsed(self):
        incident = {
            "category": "pests",
            "severity": "high",
            "incident_date": "2024-05-01",
            "source_comment_index": 2,
            "summary": "Cockroach sighted.",
            "evidence": "I saw a cockroach in the kitchen.",
        }
        raw = self._valid_json(incident_timeline=[incident])
        out = parse_reviews_response(raw)
        assert len(out.incident_timeline) == 1
        assert out.incident_timeline[0]["category"] == "pests"
        assert out.incident_timeline[0]["severity"] == "high"

    def test_recurring_issues_parsed(self):
        issue = {"category": "noise", "count": 3, "summary": "Noisy street."}
        raw = self._valid_json(recurring_issues=[issue])
        out = parse_reviews_response(raw)
        assert len(out.recurring_issues) == 1
        assert out.recurring_issues[0]["count"] == 3

    def test_conflicts_or_disputes_parsed(self):
        dispute = {"incident_date": "2024-01-10", "summary": "Refund dispute."}
        raw = self._valid_json(conflicts_or_disputes=[dispute])
        out = parse_reviews_response(raw)
        assert len(out.conflicts_or_disputes) == 1

    def test_critical_red_flags_parsed(self):
        raw = self._valid_json(critical_red_flags=["Cockroach mention in multiple reviews"])
        out = parse_reviews_response(raw)
        assert out.critical_red_flags == ["Cockroach mention in multiple reviews"]

    def test_strips_code_fences(self):
        inner = self._valid_json()
        raw = f"```json\n{inner}\n```"
        out = parse_reviews_response(raw)
        assert out.overall_assessment == "Generally positive."

    def test_missing_fields_use_defaults(self):
        raw = '{"overall_assessment": "OK."}'
        out = parse_reviews_response(raw)
        assert out.overall_risk_level == ""
        assert out.confidence == ""
        assert out.incident_timeline == []
        assert out.recurring_issues == []
        assert out.conflicts_or_disputes == []
        assert out.critical_red_flags == []
        assert out.positive_signals == []
        assert out.window_view_summary == ""

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError, match="not valid JSON"):
            parse_reviews_response("not json")

    def test_non_object_raises(self):
        with pytest.raises(ValueError, match="JSON object"):
            parse_reviews_response("[1, 2, 3]")

    def test_invalid_list_fields_default_to_empty(self):
        import json
        raw = json.dumps({
            "overall_assessment": "OK.",
            "incident_timeline": "should be list",
            "critical_red_flags": 42,
        })
        out = parse_reviews_response(raw)
        assert out.incident_timeline == []
        assert out.critical_red_flags == []

    def test_non_string_overall_assessment_defaults_to_empty(self):
        import json
        raw = json.dumps({"overall_assessment": 123})
        out = parse_reviews_response(raw)
        assert out.overall_assessment == ""

    def test_non_dict_items_in_timeline_excluded(self):
        import json
        raw = json.dumps({
            "overall_assessment": "OK.",
            "incident_timeline": [{"category": "pests"}, "not a dict", None],
        })
        out = parse_reviews_response(raw)
        assert len(out.incident_timeline) == 1


# ---------------------------------------------------------------------------
# ReviewAnalysisService (now uses ReviewCorpus)
# ---------------------------------------------------------------------------


class TestReviewAnalysisService:
    @pytest.mark.asyncio
    async def test_calls_openrouter_and_returns_output(self):
        import json
        from src.analysis.openrouter_client import OpenRouterClient

        response_json = json.dumps({
            "overall_assessment": "Lovely.",
            "overall_risk_level": "low",
            "confidence": "high",
            "incident_timeline": [],
            "recurring_issues": [],
            "conflicts_or_disputes": [],
            "critical_red_flags": [],
            "positive_signals": ["Quiet"],
            "window_view_summary": "",
        })
        mock_client = MagicMock(spec=OpenRouterClient)
        mock_client.chat = AsyncMock(return_value=response_json)
        settings = MagicMock()
        svc = ReviewAnalysisService(settings=settings, client=mock_client)
        corpus = ReviewCorpus(
            source_provider="airbnb",
            total_review_count=1,
            average_rating=5.0,
            comments=[
                UnifiedReviewComment(source_provider="airbnb", comment_text="Very nice place!")
            ],
        )
        out = await svc.analyse(corpus)
        assert out.overall_assessment == "Lovely."
        assert out.overall_risk_level == "low"
        assert out.positive_signals == ["Quiet"]
        mock_client.chat.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_prompt_sent_as_user_message_with_corpus(self):
        import json
        from src.analysis.openrouter_client import OpenRouterClient

        response_json = json.dumps({
            "overall_assessment": "OK.",
            "overall_risk_level": "low",
            "confidence": "medium",
            "incident_timeline": [],
            "recurring_issues": [],
            "conflicts_or_disputes": [],
            "critical_red_flags": [],
            "positive_signals": [],
            "window_view_summary": "",
        })
        mock_client = MagicMock(spec=OpenRouterClient)
        mock_client.chat = AsyncMock(return_value=response_json)
        settings = MagicMock()
        svc = ReviewAnalysisService(settings=settings, client=mock_client)
        corpus = ReviewCorpus(
            source_provider="airbnb",
            total_review_count=1,
            comments=[UnifiedReviewComment(source_provider="airbnb", comment_text="Fine.")],
        )
        await svc.analyse(corpus)
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
        corpus = ReviewCorpus(
            source_provider="airbnb",
            comments=[UnifiedReviewComment(source_provider="airbnb", comment_text="Test.")],
        )
        with pytest.raises(OpenRouterError, match="API down"):
            await svc.analyse(corpus)

    @pytest.mark.asyncio
    async def test_propagates_parse_error(self):
        from src.analysis.openrouter_client import OpenRouterClient

        mock_client = MagicMock(spec=OpenRouterClient)
        mock_client.chat = AsyncMock(return_value="not json at all")
        settings = MagicMock()
        svc = ReviewAnalysisService(settings=settings, client=mock_client)
        corpus = ReviewCorpus(
            source_provider="airbnb",
            comments=[UnifiedReviewComment(source_provider="airbnb", comment_text="Test.")],
        )
        with pytest.raises(ValueError):
            await svc.analyse(corpus)


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
    async def test_run_with_raw_payload_and_comments_calls_ai(self):
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
        assert result.overall_assessment == "Generally positive stay."
        assert result.overall_risk_level == "low"
        assert result.positive_signals == ["Clean", "Good location"]
        svc.analyse.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_run_without_raw_payload_falls_back_to_generic(self):
        svc = _make_review_service()
        mod = AirbnbReviewsModule(service=svc)
        ctx = AnalysisContext(listing=_listing(review_count=5, rating=4.0))
        result = await mod.run(ctx)
        # No comment texts → no AI call
        svc.analyse.assert_not_awaited()
        assert result.review_count == 5
        assert result.average_rating == pytest.approx(4.0)

    @pytest.mark.asyncio
    async def test_run_skips_ai_when_no_comment_texts(self):
        svc = _make_review_service()
        mod = AirbnbReviewsModule(service=svc)
        payload = {"reviews": [], "reviewsCount": 0}
        ctx = AnalysisContext(
            listing=_listing(),
            raw_payload=_raw_payload(payload),
        )
        result = await mod.run(ctx)
        svc.analyse.assert_not_awaited()
        assert result.overall_assessment is None

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

    @pytest.mark.asyncio
    async def test_run_returns_window_view_summary(self):
        svc = _make_review_service()
        mod = AirbnbReviewsModule(service=svc)
        payload = {"reviews": [{"comments": "Nice view."}], "reviewsCount": 1}
        ctx = AnalysisContext(listing=_listing(), raw_payload=_raw_payload(payload))
        result = await mod.run(ctx)
        assert result.window_view_summary == "City view mentioned by several guests."


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
        assert result.overall_assessment is None
        assert result.incident_timeline == []
        assert result.critical_red_flags == []

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
        from src.analysis.openrouter_client import OpenRouterError

        svc = MagicMock(spec=ReviewAnalysisService)
        svc.analyse = AsyncMock(side_effect=OpenRouterError("API down"))
        mod = AirbnbReviewsModule(service=svc)

        payload = {"reviews": [{"comments": "Great!"}], "reviewsCount": 5, "starRating": 4.5}
        ctx = AnalysisContext(listing=_listing(), raw_payload=_raw_payload(payload))

        result = await mod.run(ctx)

        assert isinstance(result, ReviewsResult)
        assert result.module_name == "reviews"
        assert result.overall_assessment is None
        assert result.incident_timeline == []
        assert result.critical_red_flags == []
        assert result.review_count == 5
        assert result.average_rating == pytest.approx(4.5)

    @pytest.mark.asyncio
    async def test_degrades_on_parse_error(self):
        svc = MagicMock(spec=ReviewAnalysisService)
        svc.analyse = AsyncMock(side_effect=ValueError("not valid JSON"))
        mod = AirbnbReviewsModule(service=svc)

        payload = {"reviews": [{"comments": "Nice spot."}], "reviewsCount": 3}
        ctx = AnalysisContext(
            listing=_listing(review_count=3, rating=4.0), raw_payload=_raw_payload(payload)
        )

        result = await mod.run(ctx)

        assert isinstance(result, ReviewsResult)
        assert result.overall_assessment is None
        assert result.incident_timeline == []

    @pytest.mark.asyncio
    async def test_job_not_blocked_when_reviews_fail(self):
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
        assert results[0].overall_assessment is None


# ---------------------------------------------------------------------------
# AirbnbReviewsModule — dedicated reviews source (Slice 2)
# ---------------------------------------------------------------------------


def _make_review_source(items=None, error=None):
    """Build a mock AirbnbReviewSource."""
    from src.analysis.reviews.airbnb_source import AirbnbReviewSource
    from src.analysis.reviews.normalizers.airbnb import AirbnbReviewNormalizer

    source = MagicMock(spec=AirbnbReviewSource)
    if error is not None:
        source.fetch = AsyncMock(side_effect=error)
    else:
        normalizer = AirbnbReviewNormalizer()
        async def _fetch(_listing_url, listing):
            return normalizer.normalize_from_actor_items(items or [], listing)
        source.fetch = AsyncMock(side_effect=_fetch)
    return source


_ACTOR_REVIEW_ITEM = {
    "id": "rv-1",
    "language": "en",
    "text": "Excellent stay, highly recommend!",
    "localizedDate": "March 2024",
    "createdAt": "2024-03-15",
    "localizedReviewerLocation": "London",
    "reviewer": {"firstName": "Alice"},
    "rating": 5,
    "response": "Thanks Alice!",
    "reviewHighlight": None,
    "startUrl": "https://www.airbnb.com/rooms/1",
}


class TestAirbnbReviewsModuleWithReviewSource:
    """AirbnbReviewsModule with a dedicated AirbnbReviewSource configured."""

    @pytest.mark.asyncio
    async def test_uses_review_source_when_available(self):
        svc = _make_review_service()
        source = _make_review_source(items=[_ACTOR_REVIEW_ITEM])
        mod = AirbnbReviewsModule(service=svc, review_source=source)

        ctx = AnalysisContext(listing=_listing())
        result = await mod.run(ctx)

        source.fetch.assert_awaited_once_with("https://www.airbnb.com/rooms/1", ctx.listing)
        assert isinstance(result, ReviewsResult)
        assert result.module_name == "reviews"
        svc.analyse.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_review_source_fetched_with_listing_url(self):
        svc = _make_review_service()
        source = _make_review_source(items=[_ACTOR_REVIEW_ITEM])
        mod = AirbnbReviewsModule(service=svc, review_source=source)
        listing = _listing()
        ctx = AnalysisContext(listing=listing)

        await mod.run(ctx)

        source.fetch.assert_awaited_once_with(listing.source_url, listing)

    @pytest.mark.asyncio
    async def test_falls_back_to_raw_payload_when_source_fails(self):
        from src.adapters.apify_client import ApifyError

        svc = _make_review_service()
        source = _make_review_source(error=ApifyError("actor error"))
        mod = AirbnbReviewsModule(service=svc, review_source=source)

        payload = {"reviews": [{"comments": "Good."}], "reviewsCount": 1}
        ctx = AnalysisContext(listing=_listing(), raw_payload=_raw_payload(payload))

        result = await mod.run(ctx)

        # Should still succeed using the listing payload fallback
        assert isinstance(result, ReviewsResult)
        svc.analyse.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_falls_back_to_generic_when_source_fails_and_no_raw_payload(self):
        from src.adapters.apify_client import ApifyError

        svc = _make_review_service()
        source = _make_review_source(error=ApifyError("actor error"))
        mod = AirbnbReviewsModule(service=svc, review_source=source)

        ctx = AnalysisContext(listing=_listing(review_count=10, rating=4.3))

        result = await mod.run(ctx)

        # No comment texts → no AI call, metadata-only result
        svc.analyse.assert_not_awaited()
        assert result.review_count == 10
        assert result.average_rating == pytest.approx(4.3)

    @pytest.mark.asyncio
    async def test_empty_actor_response_degrades_gracefully(self):
        svc = _make_review_service()
        source = _make_review_source(items=[])
        mod = AirbnbReviewsModule(service=svc, review_source=source)

        ctx = AnalysisContext(listing=_listing(review_count=5, rating=4.0))
        result = await mod.run(ctx)

        svc.analyse.assert_not_awaited()
        assert result.review_count == 5
        assert result.average_rating == pytest.approx(4.0)
        assert result.overall_assessment is None

    @pytest.mark.asyncio
    async def test_no_review_source_still_uses_raw_payload(self):
        """Backward compat: no review_source falls back to raw payload as before."""
        svc = _make_review_service()
        mod = AirbnbReviewsModule(service=svc, review_source=None)

        payload = {"reviews": [{"comments": "Great."}], "reviewsCount": 1, "starRating": 5.0}
        ctx = AnalysisContext(listing=_listing(), raw_payload=_raw_payload(payload))

        result = await mod.run(ctx)

        assert isinstance(result, ReviewsResult)
        svc.analyse.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_actor_reviews_ai_analysis_result_fields_populated(self):
        svc = _make_review_service()
        source = _make_review_source(items=[_ACTOR_REVIEW_ITEM])
        mod = AirbnbReviewsModule(service=svc, review_source=source)

        ctx = AnalysisContext(listing=_listing())
        result = await mod.run(ctx)

        assert result.overall_assessment == "Generally positive stay."
        assert result.overall_risk_level == "low"
        assert result.positive_signals == ["Clean", "Good location"]
        assert result.window_view_summary == "City view mentioned by several guests."

    @pytest.mark.asyncio
    async def test_review_source_not_called_when_listing_url_absent(self):
        """Source should not be called when listing has no URL."""
        svc = _make_review_service()
        source = _make_review_source(items=[_ACTOR_REVIEW_ITEM])
        mod = AirbnbReviewsModule(service=svc, review_source=source)

        listing = NormalizedListing(
            provider=ListingProvider.AIRBNB,
            source_url="",
            source_id="1",
            title="Test",
        )
        ctx = AnalysisContext(listing=listing)

        await mod.run(ctx)

        source.fetch.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_degrades_on_ai_failure_after_actor_fetch(self):
        from src.analysis.openrouter_client import OpenRouterError

        svc = MagicMock(spec=ReviewAnalysisService)
        svc.analyse = AsyncMock(side_effect=OpenRouterError("API down"))
        source = _make_review_source(items=[_ACTOR_REVIEW_ITEM])
        mod = AirbnbReviewsModule(service=svc, review_source=source)

        ctx = AnalysisContext(listing=_listing(review_count=10, rating=4.5))
        result = await mod.run(ctx)

        assert result.overall_assessment is None
        assert result.incident_timeline == []
        assert result.review_count == 10
        assert result.average_rating == pytest.approx(4.5)
