"""Tests for the AI analysis flow.

Covers:
- OpenRouterClient.chat — success, non-200 error, malformed response shapes
- parse_analysis_response — valid JSON, JSON in fences, bad JSON, unknown verdict
- build_prompt — key fields appear in the prompt
- AnalysisService.analyse — successful round-trip, OpenRouterError propagation,
  ValueError propagation for unparseable response
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.analysis.openrouter_client import OpenRouterClient, OpenRouterError
from src.analysis.result import AnalysisResult, PriceVerdict
from src.analysis.service import AnalysisService, build_prompt, parse_analysis_response
from src.app.config import Settings
from src.domain.listing import (
    ListingLocation,
    ListingProvider,
    NormalizedListing,
    PriceInfo,
)
from src.enrichment.runner import EnrichmentOutcome, EnrichmentProviderResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_settings(**overrides: Any) -> Settings:
    defaults: dict[str, Any] = {
        "app_env": "testing",
        "openrouter_api_key": "test-or-key",
        "openrouter_model": "anthropic/claude-3-haiku",
    }
    defaults.update(overrides)
    return Settings(**defaults)


def _minimal_listing(**overrides: Any) -> NormalizedListing:
    base: dict[str, Any] = {
        "provider": ListingProvider.AIRBNB,
        "source_url": "https://www.airbnb.com/rooms/12345",
        "source_id": "12345",
        "title": "Cozy Studio in Paris",
    }
    base.update(overrides)
    return NormalizedListing(**base)


def _full_listing() -> NormalizedListing:
    return NormalizedListing(
        provider=ListingProvider.AIRBNB,
        source_url="https://www.airbnb.com/rooms/12345",
        source_id="12345",
        title="Cozy Studio in Paris",
        description="A wonderful place to stay near the Eiffel Tower.",
        location=ListingLocation(
            latitude=48.8566,
            longitude=2.3522,
            city="Paris",
            country="France",
            neighbourhood="Le Marais",
        ),
        price=PriceInfo(amount=Decimal("85"), currency="USD", period="night"),
        bedrooms=1,
        bathrooms=1.0,
        max_guests=2,
        amenities=["WiFi", "Kitchen"],
        rating=4.87,
        review_count=156,
        host_name="Marie",
        host_is_superhost=True,
    )


def _valid_analysis_json() -> str:
    return json.dumps(
        {
            "summary": "A charming studio in central Paris.",
            "strengths": ["Great location", "Superhost"],
            "risks": ["Small space", "Steep cleaning fee"],
            "price_verdict": "fair",
            "price_explanation": "Price is in line with similar Paris studios.",
        }
    )


# ---------------------------------------------------------------------------
# OpenRouterClient
# ---------------------------------------------------------------------------


class TestOpenRouterClientSuccess:
    @pytest.mark.asyncio
    async def test_returns_content_on_200(self):
        body = {
            "choices": [{"message": {"role": "assistant", "content": "Hello!"}}]
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = body

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = OpenRouterClient(api_key="key", model="test/model")
            result = await client.chat([{"role": "user", "content": "Hi"}])

        assert result == "Hello!"

    @pytest.mark.asyncio
    async def test_sends_bearer_auth_header(self):
        body = {"choices": [{"message": {"content": "ok"}}]}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = body

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = OpenRouterClient(api_key="my-secret-key", model="test/model")
            await client.chat([{"role": "user", "content": "x"}])

        call_kwargs = mock_client.post.call_args
        assert call_kwargs.kwargs["headers"]["Authorization"] == "Bearer my-secret-key"

    @pytest.mark.asyncio
    async def test_sends_model_in_payload(self):
        body = {"choices": [{"message": {"content": "ok"}}]}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = body

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = OpenRouterClient(api_key="key", model="anthropic/claude-3-haiku")
            await client.chat([{"role": "user", "content": "x"}])

        sent_json = mock_client.post.call_args.kwargs["json"]
        assert sent_json["model"] == "anthropic/claude-3-haiku"


class TestOpenRouterClientErrors:
    @pytest.mark.asyncio
    async def test_raises_on_non_200(self):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = OpenRouterClient(api_key="key", model="m")
            with pytest.raises(OpenRouterError, match="401"):
                await client.chat([])

    @pytest.mark.asyncio
    async def test_raises_on_missing_choices(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "abc"}  # no 'choices'

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = OpenRouterClient(api_key="key", model="m")
            with pytest.raises(OpenRouterError, match="choices"):
                await client.chat([])

    @pytest.mark.asyncio
    async def test_raises_on_empty_choices(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = OpenRouterClient(api_key="key", model="m")
            with pytest.raises(OpenRouterError, match="choices"):
                await client.chat([])

    @pytest.mark.asyncio
    async def test_raises_on_non_string_content(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": None}}]
        }

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = OpenRouterClient(api_key="key", model="m")
            with pytest.raises(OpenRouterError, match="content"):
                await client.chat([])

    @pytest.mark.asyncio
    async def test_raises_on_non_dict_body(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["unexpected", "list"]

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = OpenRouterClient(api_key="key", model="m")
            with pytest.raises(OpenRouterError, match="Unexpected"):
                await client.chat([])

    @pytest.mark.asyncio
    async def test_timeout_raises_openrouter_error(self):
        import httpx as _httpx

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=_httpx.TimeoutException("timed out"))
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = OpenRouterClient(api_key="key", model="m", timeout=5.0)
            with pytest.raises(OpenRouterError, match="timed out"):
                await client.chat([])

    @pytest.mark.asyncio
    async def test_connect_error_raises_openrouter_error(self):
        import httpx as _httpx

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=_httpx.ConnectError("Connection refused")
            )
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            client = OpenRouterClient(api_key="key", model="m")
            with pytest.raises(OpenRouterError, match="Connection refused"):
                await client.chat([])


# ---------------------------------------------------------------------------
# parse_analysis_response
# ---------------------------------------------------------------------------


class TestParseAnalysisResponse:
    def test_valid_json_parses_correctly(self):
        result = parse_analysis_response(_valid_analysis_json())

        assert isinstance(result, AnalysisResult)
        assert result.summary == "A charming studio in central Paris."
        assert result.strengths == ["Great location", "Superhost"]
        assert result.risks == ["Small space", "Steep cleaning fee"]
        assert result.price_verdict == PriceVerdict.FAIR
        assert "Paris" in result.price_explanation

    def test_strips_json_code_fence(self):
        fenced = "```json\n" + _valid_analysis_json() + "\n```"
        result = parse_analysis_response(fenced)
        assert result.price_verdict == PriceVerdict.FAIR

    def test_strips_plain_code_fence(self):
        fenced = "```\n" + _valid_analysis_json() + "\n```"
        result = parse_analysis_response(fenced)
        assert result.summary == "A charming studio in central Paris."

    def test_unknown_price_verdict_falls_back(self):
        data = json.loads(_valid_analysis_json())
        data["price_verdict"] = "completely_made_up"
        result = parse_analysis_response(json.dumps(data))
        assert result.price_verdict == PriceVerdict.UNKNOWN

    def test_overpriced_verdict_accepted(self):
        data = json.loads(_valid_analysis_json())
        data["price_verdict"] = "overpriced"
        result = parse_analysis_response(json.dumps(data))
        assert result.price_verdict == PriceVerdict.OVERPRICED

    def test_underpriced_verdict_accepted(self):
        data = json.loads(_valid_analysis_json())
        data["price_verdict"] = "underpriced"
        result = parse_analysis_response(json.dumps(data))
        assert result.price_verdict == PriceVerdict.UNDERPRICED

    def test_missing_optional_fields_use_defaults(self):
        minimal = json.dumps({"summary": "Short summary."})
        result = parse_analysis_response(minimal)
        assert result.summary == "Short summary."
        assert result.strengths == []
        assert result.risks == []
        assert result.price_verdict == PriceVerdict.UNKNOWN
        assert result.price_explanation == ""

    def test_raises_value_error_on_invalid_json(self):
        with pytest.raises(ValueError, match="not valid JSON"):
            parse_analysis_response("this is not JSON at all")

    def test_raises_value_error_on_json_array(self):
        with pytest.raises(ValueError, match="Expected a JSON object"):
            parse_analysis_response("[1, 2, 3]")

    def test_non_string_list_items_filtered(self):
        data = {
            "summary": "Test.",
            "strengths": ["good", 42, None, "also good"],
            "risks": [],
            "price_verdict": "unknown",
            "price_explanation": "",
        }
        result = parse_analysis_response(json.dumps(data))
        # Only actual strings should appear
        assert result.strengths == ["good", "also good"]

    def test_raises_when_summary_missing(self):
        data = {
            "strengths": ["fine"],
            "risks": [],
            "price_verdict": "fair",
            "price_explanation": "ok",
        }
        with pytest.raises(ValueError, match="summary"):
            parse_analysis_response(json.dumps(data))

    def test_raises_when_summary_empty_string(self):
        data = {
            "summary": "",
            "strengths": [],
            "risks": [],
            "price_verdict": "fair",
            "price_explanation": "ok",
        }
        with pytest.raises(ValueError, match="summary"):
            parse_analysis_response(json.dumps(data))

    def test_raises_when_summary_whitespace_only(self):
        data = {"summary": "   "}
        with pytest.raises(ValueError, match="summary"):
            parse_analysis_response(json.dumps(data))

    def test_raises_when_summary_is_non_string(self):
        data = {"summary": 42}
        with pytest.raises(ValueError, match="summary"):
            parse_analysis_response(json.dumps(data))

    def test_raises_when_strengths_not_a_list(self):
        data = {
            "summary": "Good place.",
            "strengths": "should be a list",
            "risks": [],
            "price_verdict": "fair",
            "price_explanation": "ok",
        }
        with pytest.raises(ValueError, match="strengths"):
            parse_analysis_response(json.dumps(data))

    def test_raises_when_risks_not_a_list(self):
        data = {
            "summary": "Good place.",
            "strengths": [],
            "risks": {"unexpected": "dict"},
            "price_verdict": "fair",
            "price_explanation": "ok",
        }
        with pytest.raises(ValueError, match="risks"):
            parse_analysis_response(json.dumps(data))


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------


class TestBuildPrompt:
    def test_title_always_present(self):
        prompt = build_prompt(_minimal_listing())
        assert "Cozy Studio in Paris" in prompt

    def test_full_listing_includes_key_fields(self):
        prompt = build_prompt(_full_listing())
        assert "Paris" in prompt
        assert "85" in prompt
        assert "USD" in prompt
        assert "night" in prompt
        assert "Bedrooms: 1" in prompt
        assert "WiFi" in prompt
        assert "4.87" in prompt
        assert "156" in prompt
        assert "Marie" in prompt
        assert "Superhost" in prompt

    def test_description_included_when_present(self):
        prompt = build_prompt(_full_listing())
        assert "Eiffel Tower" in prompt

    def test_long_description_truncated(self):
        long_desc = "x" * 700
        listing = _minimal_listing(description=long_desc)
        prompt = build_prompt(listing)
        # The description snippet is 600 chars + ellipsis, not the full 700
        assert long_desc not in prompt
        assert "…" in prompt

    def test_missing_optional_fields_absent(self):
        prompt = build_prompt(_minimal_listing())
        assert "Price:" not in prompt
        assert "Bedrooms:" not in prompt
        assert "Rating:" not in prompt

    def test_prompt_requests_json_schema(self):
        prompt = build_prompt(_minimal_listing())
        assert "price_verdict" in prompt
        assert "summary" in prompt

    def test_no_enrichment_section_when_enrichment_is_none(self):
        prompt = build_prompt(_minimal_listing(), enrichment=None)
        assert "Nearby context" not in prompt

    def test_no_enrichment_section_when_all_enrichments_failed(self):
        outcome = EnrichmentOutcome(
            successes=[],
            failures=[EnrichmentProviderResult(name="transport", error=RuntimeError("down"))],
        )
        prompt = build_prompt(_minimal_listing(), enrichment=outcome)
        assert "Nearby context" not in prompt

    def test_transport_enrichment_appears_in_prompt(self):
        transport_result = EnrichmentProviderResult(
            name="transport",
            data={"count": 3, "nearest_name": "Châtelet", "nearest_distance_m": 120.0, "categories_found": ["public_transport"]},
        )
        outcome = EnrichmentOutcome(successes=[transport_result])
        prompt = build_prompt(_minimal_listing(), enrichment=outcome)
        assert "Nearby context" in prompt
        assert "Transport" in prompt
        assert "3 public transport stop(s)" in prompt
        assert "Châtelet" in prompt

    def test_nearby_places_enrichment_appears_in_prompt(self):
        places_result = EnrichmentProviderResult(
            name="nearby_places",
            data={"count": 10, "by_category": {"shops": 3, "restaurants_cafes": 5, "parks": 2}},
        )
        outcome = EnrichmentOutcome(successes=[places_result])
        prompt = build_prompt(_minimal_listing(), enrichment=outcome)
        assert "Nearby context" in prompt
        assert "Nearby places" in prompt
        assert "10 total within 500 m" in prompt
        assert "shops: 3" in prompt

    def test_both_enrichments_appear_in_prompt(self):
        outcome = EnrichmentOutcome(
            successes=[
                EnrichmentProviderResult(
                    name="transport",
                    data={"count": 2, "nearest_name": None, "nearest_distance_m": None, "categories_found": []},
                ),
                EnrichmentProviderResult(
                    name="nearby_places",
                    data={"count": 5, "by_category": {"parks": 2}},
                ),
            ]
        )
        prompt = build_prompt(_minimal_listing(), enrichment=outcome)
        assert "Transport" in prompt
        assert "Nearby places" in prompt

    def test_transport_without_nearest_name_omits_nearest(self):
        transport_result = EnrichmentProviderResult(
            name="transport",
            data={"count": 1, "nearest_name": None, "nearest_distance_m": None, "categories_found": []},
        )
        outcome = EnrichmentOutcome(successes=[transport_result])
        prompt = build_prompt(_minimal_listing(), enrichment=outcome)
        assert "nearest:" not in prompt


# ---------------------------------------------------------------------------
# AnalysisService
# ---------------------------------------------------------------------------


class TestAnalysisService:
    def _service(self, mock_client: AsyncMock | None = None) -> tuple[AnalysisService, AsyncMock]:
        chat_mock = mock_client or AsyncMock()
        client = MagicMock(spec=OpenRouterClient)
        client.chat = chat_mock
        return AnalysisService(settings=_make_settings(), client=client), chat_mock

    @pytest.mark.asyncio
    async def test_analyse_returns_result_on_success(self):
        service, mock_chat = self._service()
        mock_chat.return_value = _valid_analysis_json()

        result = await service.analyse(_full_listing())

        assert isinstance(result, AnalysisResult)
        assert result.price_verdict == PriceVerdict.FAIR
        assert result.summary != ""

    @pytest.mark.asyncio
    async def test_analyse_passes_system_and_user_messages(self):
        service, mock_chat = self._service()
        mock_chat.return_value = _valid_analysis_json()

        await service.analyse(_full_listing())

        messages = mock_chat.call_args.args[0]
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Cozy Studio in Paris" in messages[1]["content"]

    @pytest.mark.asyncio
    async def test_analyse_propagates_openrouter_error(self):
        service, mock_chat = self._service()
        mock_chat.side_effect = OpenRouterError("network failure")

        with pytest.raises(OpenRouterError, match="network failure"):
            await service.analyse(_full_listing())

    @pytest.mark.asyncio
    async def test_analyse_propagates_parse_error(self):
        service, mock_chat = self._service()
        mock_chat.return_value = "not valid json {{ }}"

        with pytest.raises(ValueError, match="not valid JSON"):
            await service.analyse(_full_listing())

    @pytest.mark.asyncio
    async def test_analyse_includes_enrichment_in_prompt(self):
        """Enrichment data reaches the user-turn prompt content."""
        service, mock_chat = self._service()
        mock_chat.return_value = _valid_analysis_json()

        transport_result = EnrichmentProviderResult(
            name="transport",
            data={"count": 4, "nearest_name": "Gare du Nord", "nearest_distance_m": 80.0, "categories_found": ["public_transport"]},
        )
        outcome = EnrichmentOutcome(successes=[transport_result])

        await service.analyse(_full_listing(), enrichment=outcome)

        messages = mock_chat.call_args.args[0]
        user_content = messages[1]["content"]
        assert "Gare du Nord" in user_content
        assert "4 public transport stop(s)" in user_content


# ---------------------------------------------------------------------------
# Settings validation
# ---------------------------------------------------------------------------


class TestSettingsOpenRouterValidation:
    def test_openrouter_api_key_required_outside_dev(self):
        with pytest.raises(ValueError, match="openrouter_api_key"):
            Settings(
                app_env="production",
                telegram_bot_token="tok",
                telegram_webhook_secret="sec",
                apify_api_token="apify",
                openrouter_api_key="",  # empty — should fail
            )

    def test_openrouter_api_key_not_required_in_testing(self):
        s = Settings(app_env="testing", openrouter_api_key="")
        assert s.openrouter_api_key == ""

    def test_openrouter_api_key_not_required_in_development(self):
        s = Settings(app_env="development", openrouter_api_key="")
        assert s.openrouter_api_key == ""

    def test_openrouter_api_key_accepted_in_production(self):
        s = Settings(
            app_env="production",
            telegram_bot_token="tok",
            telegram_webhook_secret="sec",
            apify_api_token="apify",
            openrouter_api_key="or-key",
            openrouter_model="anthropic/claude-3-haiku",
        )
        assert s.openrouter_api_key == "or-key"
        assert s.openrouter_model == "anthropic/claude-3-haiku"

    def test_openrouter_model_required_outside_dev(self):
        with pytest.raises(ValueError, match="openrouter_model"):
            Settings(
                app_env="production",
                telegram_bot_token="tok",
                telegram_webhook_secret="sec",
                apify_api_token="apify",
                openrouter_api_key="or-key",
                openrouter_model="",  # empty — should fail
            )

    def test_openrouter_model_not_required_in_testing(self):
        s = Settings(app_env="testing", openrouter_model="")
        assert s.openrouter_model == ""

    def test_openrouter_model_not_required_in_development(self):
        s = Settings(app_env="development", openrouter_model="")
        assert s.openrouter_model == ""
