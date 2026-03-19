"""Tests for the on-demand translation service."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.analysis.result import AnalysisResult, PriceVerdict
from src.i18n.types import Language
from src.translation.service import (
    TranslationError,
    TranslationService,
    _build_translation_prompt,
    _parse_translation_response,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(**overrides) -> AnalysisResult:
    base = {
        "summary": "A well-located flat with modern amenities.",
        "strengths": ["Great location", "Modern kitchen"],
        "risks": ["Noisy street", "Steep cleaning fee"],
        "price_verdict": PriceVerdict.FAIR,
        "price_explanation": "Price is in line with comparable listings.",
    }
    base.update(overrides)
    return AnalysisResult(**base)


def _make_settings(**overrides):
    from src.app.config import Settings

    defaults = dict(
        app_env="testing",
        telegram_bot_token="test-bot-token",
        openrouter_api_key="test-key",
        apify_api_token="test-apify",
    )
    defaults.update(overrides)
    return Settings(**defaults)


# ---------------------------------------------------------------------------
# _build_translation_prompt
# ---------------------------------------------------------------------------


class TestBuildTranslationPrompt:
    def test_prompt_includes_target_language_name(self):
        result = _make_result()
        prompt = _build_translation_prompt(result, Language.RU)
        assert "Russian" in prompt

    def test_prompt_includes_spanish_language_name(self):
        result = _make_result()
        prompt = _build_translation_prompt(result, Language.ES)
        assert "Spanish" in prompt

    def test_prompt_contains_source_summary(self):
        result = _make_result()
        prompt = _build_translation_prompt(result, Language.RU)
        assert result.summary in prompt

    def test_prompt_contains_source_strengths(self):
        result = _make_result()
        prompt = _build_translation_prompt(result, Language.RU)
        assert "Great location" in prompt
        assert "Modern kitchen" in prompt

    def test_prompt_contains_source_risks(self):
        result = _make_result()
        prompt = _build_translation_prompt(result, Language.RU)
        assert "Noisy street" in prompt

    def test_prompt_contains_source_price_explanation(self):
        result = _make_result()
        prompt = _build_translation_prompt(result, Language.RU)
        assert result.price_explanation in prompt

    def test_prompt_does_not_include_price_verdict_key(self):
        """price_verdict is language-neutral and must not appear as a field to translate."""
        result = _make_result(price_verdict=PriceVerdict.OVERPRICED)
        prompt = _build_translation_prompt(result, Language.RU)
        # Extract the Input JSON block (after "Input:\n" and before "\n\nOutput schema:")
        input_section = prompt.split("Output schema:")[0]
        input_json_start = input_section.find("{")
        source = json.loads(input_section[input_json_start:])
        assert "price_verdict" not in source


# ---------------------------------------------------------------------------
# _parse_translation_response
# ---------------------------------------------------------------------------


class TestParseTranslationResponse:
    def _original(self) -> AnalysisResult:
        return _make_result()

    def test_parses_valid_json(self):
        payload = {
            "summary": "Хорошая квартира в центре.",
            "strengths": ["Отличное расположение", "Современная кухня"],
            "risks": ["Шумная улица", "Высокая плата за уборку"],
            "price_explanation": "Цена соответствует аналогам.",
        }
        result = _parse_translation_response(json.dumps(payload), self._original())
        assert result.summary == "Хорошая квартира в центре."
        assert result.strengths == ["Отличное расположение", "Современная кухня"]
        assert result.risks == ["Шумная улица", "Высокая плата за уборку"]
        assert result.price_explanation == "Цена соответствует аналогам."

    def test_price_verdict_preserved_from_original(self):
        payload = {
            "summary": "Translated.",
            "strengths": [],
            "risks": [],
            "price_explanation": "Translated explanation.",
        }
        original = _make_result(price_verdict=PriceVerdict.OVERPRICED)
        result = _parse_translation_response(json.dumps(payload), original)
        assert result.price_verdict == PriceVerdict.OVERPRICED

    def test_strips_json_fences(self):
        raw = '```json\n{"summary": "Test.", "strengths": [], "risks": [], "price_explanation": "Ok."}\n```'
        original = self._original()
        result = _parse_translation_response(raw, original)
        assert result.summary == "Test."

    def test_raises_on_non_json(self):
        with pytest.raises(TranslationError, match="not valid JSON"):
            _parse_translation_response("not json at all", self._original())

    def test_raises_on_json_array(self):
        with pytest.raises(TranslationError, match="JSON object"):
            _parse_translation_response("[1, 2, 3]", self._original())

    def test_falls_back_to_original_summary_when_missing(self):
        """Missing 'summary' must fall back to original and not raise."""
        payload = {
            "strengths": ["x"],
            "risks": [],
            "price_explanation": "y",
        }
        original = self._original()
        result = _parse_translation_response(json.dumps(payload), original)
        assert result.summary == original.summary

    def test_falls_back_to_original_strengths_when_not_a_list(self):
        payload = {
            "summary": "Translated.",
            "strengths": "not a list",
            "risks": [],
            "price_explanation": "y",
        }
        original = self._original()
        result = _parse_translation_response(json.dumps(payload), original)
        assert result.strengths == original.strengths

    def test_falls_back_to_original_risks_when_not_a_list(self):
        payload = {
            "summary": "Translated.",
            "strengths": [],
            "risks": 42,
            "price_explanation": "y",
        }
        original = self._original()
        result = _parse_translation_response(json.dumps(payload), original)
        assert result.risks == original.risks

    def test_falls_back_to_original_strengths_when_all_items_invalid(self):
        payload = {
            "summary": "Translated.",
            "strengths": [1, 2, 3],
            "risks": [],
            "price_explanation": "y",
        }
        original = self._original()
        result = _parse_translation_response(json.dumps(payload), original)
        assert result.strengths == original.strengths


# ---------------------------------------------------------------------------
# TranslationService.translate — English passthrough
# ---------------------------------------------------------------------------


class TestTranslationServiceEnglishPassthrough:
    @pytest.mark.asyncio
    async def test_english_result_returned_as_is_without_llm_call(self):
        """For Language.EN, the original result is returned without any LLM call."""
        mock_client = AsyncMock()
        settings = _make_settings()
        service = TranslationService(settings, client=mock_client)
        original = _make_result()

        returned = await service.translate(original, Language.EN)

        assert returned is original
        mock_client.chat.assert_not_awaited()


# ---------------------------------------------------------------------------
# TranslationService.translate — non-English paths
# ---------------------------------------------------------------------------


class TestTranslationServiceNonEnglish:
    def _ru_payload(self) -> str:
        return json.dumps(
            {
                "summary": "Хорошая квартира в центре.",
                "strengths": ["Отличное расположение"],
                "risks": ["Шумная улица"],
                "price_explanation": "Цена соответствует аналогам.",
            }
        )

    @pytest.mark.asyncio
    async def test_translate_ru_calls_llm_once(self):
        mock_client = AsyncMock()
        mock_client.chat.return_value = self._ru_payload()
        settings = _make_settings()
        service = TranslationService(settings, client=mock_client)
        original = _make_result()

        await service.translate(original, Language.RU)

        mock_client.chat.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_translate_ru_returns_translated_summary(self):
        mock_client = AsyncMock()
        mock_client.chat.return_value = self._ru_payload()
        settings = _make_settings()
        service = TranslationService(settings, client=mock_client)
        original = _make_result()

        result = await service.translate(original, Language.RU)

        assert result.summary == "Хорошая квартира в центре."

    @pytest.mark.asyncio
    async def test_translate_result_is_not_same_object_as_original(self):
        mock_client = AsyncMock()
        mock_client.chat.return_value = self._ru_payload()
        settings = _make_settings()
        service = TranslationService(settings, client=mock_client)
        original = _make_result()

        result = await service.translate(original, Language.RU)

        assert result is not original

    @pytest.mark.asyncio
    async def test_translate_preserves_price_verdict(self):
        mock_client = AsyncMock()
        mock_client.chat.return_value = self._ru_payload()
        settings = _make_settings()
        service = TranslationService(settings, client=mock_client)
        original = _make_result(price_verdict=PriceVerdict.OVERPRICED)

        result = await service.translate(original, Language.RU)

        assert result.price_verdict == PriceVerdict.OVERPRICED

    @pytest.mark.asyncio
    async def test_translate_es_calls_llm_with_spanish_prompt(self):
        mock_client = AsyncMock()
        mock_client.chat.return_value = json.dumps(
            {
                "summary": "Un apartamento agradable.",
                "strengths": ["Buena ubicación"],
                "risks": ["Calle ruidosa"],
                "price_explanation": "El precio es adecuado.",
            }
        )
        settings = _make_settings()
        service = TranslationService(settings, client=mock_client)
        original = _make_result()

        result = await service.translate(original, Language.ES)

        assert result.summary == "Un apartamento agradable."
        # Verify that the LLM was asked to translate to Spanish.
        messages_sent = mock_client.chat.call_args[0][0]
        user_message = next(m["content"] for m in messages_sent if m["role"] == "user")
        assert "Spanish" in user_message

    @pytest.mark.asyncio
    async def test_translate_propagates_openrouter_error(self):
        from src.analysis.openrouter_client import OpenRouterError

        mock_client = AsyncMock()
        mock_client.chat.side_effect = OpenRouterError("OpenRouter request failed with status 500")
        settings = _make_settings()
        service = TranslationService(settings, client=mock_client)
        original = _make_result()

        with pytest.raises(OpenRouterError):
            await service.translate(original, Language.RU)

    @pytest.mark.asyncio
    async def test_translate_raises_translation_error_on_bad_response(self):
        mock_client = AsyncMock()
        mock_client.chat.return_value = "not valid json"
        settings = _make_settings()
        service = TranslationService(settings, client=mock_client)
        original = _make_result()

        with pytest.raises(TranslationError):
            await service.translate(original, Language.RU)

    @pytest.mark.asyncio
    async def test_translated_output_not_same_as_original_text(self):
        """Sanity check: translated fields differ from original English content."""
        mock_client = AsyncMock()
        mock_client.chat.return_value = self._ru_payload()
        settings = _make_settings()
        service = TranslationService(settings, client=mock_client)
        original = _make_result()

        result = await service.translate(original, Language.RU)

        assert result.summary != original.summary
