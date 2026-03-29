"""Tests for the simple amenities block (spec 031).

Covers:
- AnalysisResult carries amenities field
- Telegram formatter renders amenities as a dedicated section
- Amenities section omitted when list is empty
- All amenity items are rendered (no cap)
- Amenity strings are HTML-escaped
- i18n labels work for all supported languages
- Translation service passes amenities through (and falls back gracefully)
- Pipeline-level: listing.amenities flows through process_job into the delivered message
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.analysis.result import AnalysisResult, PriceVerdict
from src.analysis.service import AnalysisService
from src.domain.delivery import DeliveryChannel, TelegramDeliveryContext
from src.domain.listing import AnalysisJob, ListingProvider, NormalizedListing
from src.i18n.types import Language
from src.telegram.formatter import format_analysis_message
from src.translation.service import _build_translation_prompt, _parse_translation_response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _listing(**overrides) -> NormalizedListing:
    base = {
        "provider": ListingProvider.AIRBNB,
        "source_url": "https://www.airbnb.com/rooms/99",
        "source_id": "99",
        "title": "Test Apartment",
    }
    base.update(overrides)
    return NormalizedListing(**base)


def _result(**overrides) -> AnalysisResult:
    base = {
        "summary": "Nice place.",
        "price_verdict": PriceVerdict.FAIR,
    }
    base.update(overrides)
    return AnalysisResult(**base)


# ---------------------------------------------------------------------------
# AnalysisResult model
# ---------------------------------------------------------------------------


class TestAnalysisResultAmenities:
    def test_amenities_defaults_to_empty_list(self):
        r = _result()
        assert r.amenities == []

    def test_amenities_stores_given_list(self):
        r = _result(amenities=["WiFi", "Kitchen", "Pool"])
        assert r.amenities == ["WiFi", "Kitchen", "Pool"]

    def test_model_copy_preserves_amenities(self):
        r = _result(amenities=["WiFi"])
        r2 = r.model_copy(update={"summary": "Updated."})
        assert r2.amenities == ["WiFi"]


# ---------------------------------------------------------------------------
# Telegram formatter
# ---------------------------------------------------------------------------


class TestAmenitiesFormatterSection:
    def test_amenities_section_present_when_non_empty(self):
        msg = format_analysis_message(
            _listing(),
            _result(amenities=["WiFi", "Kitchen"]),
            Language.EN,
        )
        assert "<b>Amenities:</b>" in msg
        assert "WiFi" in msg
        assert "Kitchen" in msg

    def test_amenities_section_omitted_when_empty(self):
        msg = format_analysis_message(_listing(), _result(amenities=[]), Language.EN)
        assert "Amenities:" not in msg

    def test_amenities_all_items_rendered(self):
        many = [f"Item{i}" for i in range(20)]
        msg = format_analysis_message(_listing(), _result(amenities=many), Language.EN)
        # All items must appear — no cap
        assert "Item9" in msg
        assert "Item10" in msg
        assert "Item19" in msg

    def test_amenities_html_escaped(self):
        msg = format_analysis_message(
            _listing(),
            _result(amenities=["Wi-Fi & TV", "<Pool>"]),
            Language.EN,
        )
        assert "Wi-Fi &amp; TV" in msg
        assert "&lt;Pool&gt;" in msg

    def test_amenities_section_appears_after_risks(self):
        msg = format_analysis_message(
            _listing(),
            _result(
                risks=["Noisy street"],
                amenities=["WiFi", "Kitchen"],
            ),
            Language.EN,
        )
        risks_pos = msg.index("Noisy street")
        amenities_pos = msg.index("Amenities:")
        assert amenities_pos > risks_pos

    def test_russian_amenities_label(self):
        msg = format_analysis_message(
            _listing(),
            _result(amenities=["WiFi"]),
            Language.RU,
        )
        assert "<b>Удобства:</b>" in msg

    def test_spanish_amenities_label(self):
        msg = format_analysis_message(
            _listing(),
            _result(amenities=["WiFi"]),
            Language.ES,
        )
        assert "<b>Servicios:</b>" in msg

    def test_amenities_bullet_list_format(self):
        msg = format_analysis_message(
            _listing(),
            _result(amenities=["WiFi", "Kitchen", "Pool"]),
            Language.EN,
        )
        assert "- WiFi" in msg
        assert "- Kitchen" in msg
        assert "- Pool" in msg


# ---------------------------------------------------------------------------
# Translation stage
# ---------------------------------------------------------------------------


class TestAmenitiesTranslation:
    def test_amenities_not_included_in_translation_prompt(self):
        """Amenity labels are scraper verbatim strings — must not be sent to LLM."""
        r = _result(amenities=["WiFi", "Kitchen"])
        prompt = _build_translation_prompt(r, Language.RU)
        # The amenities key must not appear in the source JSON sent for translation.
        input_section = prompt.split("Output schema:")[0]
        import json as _json
        input_json_start = input_section.find("{")
        source = _json.loads(input_section[input_json_start:])
        assert "amenities" not in source

    def test_parse_response_preserves_original_amenities(self):
        """Translation response is ignored for amenities; original labels are kept as-is."""
        original = _result(amenities=["WiFi", "Kitchen"])
        response = json.dumps(
            {
                "display_title": "Test",
                "summary": "Хорошее место.",
                "strengths": [],
                "risks": [],
                "price_explanation": "",
                "review_overall_assessment": "",
                "review_critical_red_flags": [],
                "review_recurring_issues": [],
                "review_conflicts_or_disputes": [],
                "review_positive_signals": [],
                "review_window_view_summary": "",
            }
        )
        result = _parse_translation_response(response, original)
        assert result.amenities == ["WiFi", "Kitchen"]

    def test_parse_response_empty_amenities_stays_empty(self):
        original = _result(amenities=[])
        response = json.dumps(
            {
                "display_title": "Test",
                "summary": "Хорошее место.",
                "strengths": [],
                "risks": [],
                "price_explanation": "",
                "review_overall_assessment": "",
                "review_critical_red_flags": [],
                "review_recurring_issues": [],
                "review_conflicts_or_disputes": [],
                "review_positive_signals": [],
                "review_window_view_summary": "",
            }
        )
        result = _parse_translation_response(response, original)
        assert result.amenities == []


# ---------------------------------------------------------------------------
# Pipeline-level: listing.amenities → process_job → delivered message
# ---------------------------------------------------------------------------


class TestAmenitiesPipeline:
    """Verify that listing.amenities are threaded through process_job into the
    final formatted message delivered by the presenter."""

    @pytest.mark.asyncio
    async def test_listing_amenities_appear_in_delivered_message(self):
        """process_job must map listing.amenities into the assembled result and
        forward them to the Telegram message."""
        from decimal import Decimal

        from src.adapters.base import AdapterResult
        from src.app.config import Settings
        from src.jobs.processor import process_job

        amenities = ["WiFi", "Kitchen", "Pool"]

        listing = NormalizedListing(
            provider=ListingProvider.AIRBNB,
            source_url="https://www.airbnb.com/rooms/99",
            source_id="99",
            title="Test Apartment",
            amenities=amenities,
        )

        ai_result = AnalysisResult(
            summary="Great spot.",
            price_verdict=PriceVerdict.FAIR,
        )

        mock_adapter = MagicMock()
        mock_adapter.fetch = AsyncMock(
            return_value=AdapterResult(raw={"id": "99"}, listing=listing)
        )

        mock_service = MagicMock(spec=AnalysisService)
        mock_service.analyse = AsyncMock(return_value=ai_result)

        mock_ts = MagicMock()
        mock_ts.translate = AsyncMock(side_effect=lambda result, lang: result)

        settings = Settings(
            app_env="testing",
            telegram_bot_token="test-token",
            openrouter_api_key="test-key",
            apify_api_token="test-apify",
        )

        job = AnalysisJob(
            source_url="https://www.airbnb.com/rooms/99",
            provider=ListingProvider.AIRBNB,
            delivery_channel=DeliveryChannel.TELEGRAM,
            telegram_context=TelegramDeliveryContext(chat_id=42, message_id=1),
            language=Language.EN,
        )

        delivered: list[str] = []

        async def fake_send(token, chat_id, text, *, parse_mode=None, client=None):
            delivered.append(text)

        with patch("src.telegram.presenter.send_message", side_effect=fake_send):
            await process_job(
                job,
                settings,
                adapter=mock_adapter,
                analysis_service=mock_service,
                translation_service=mock_ts,
            )

        assert len(delivered) == 1
        msg = delivered[0]
        assert "WiFi" in msg
        assert "Kitchen" in msg
        assert "Pool" in msg
        assert "<b>Amenities:</b>" in msg
