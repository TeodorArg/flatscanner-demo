"""Regression tests for spec 029 — Airbnb priced URL fix.

Covers:
- _build_actor_input: canonical URL stripping, stay dates, occupancy forwarding
- _normalize: stay-level PriceInfo fields from tri_angle dated response
- build_prompt: richer stay-price context for dated stays
- format_analysis_message: stay-price block appearance
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.adapters.airbnb import _build_actor_input, _normalize
from src.analysis.result import AnalysisResult, PriceVerdict
from src.analysis.service import build_prompt
from src.domain.listing import ListingProvider, NormalizedListing, PriceInfo
from src.i18n.types import Language
from src.telegram.formatter import format_analysis_message


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _listing(**overrides) -> NormalizedListing:
    base = {
        "provider": ListingProvider.AIRBNB,
        "source_url": "https://www.airbnb.com/rooms/12345",
        "source_id": "12345",
        "title": "Test Flat",
    }
    base.update(overrides)
    return NormalizedListing(**base)


def _result(**overrides) -> AnalysisResult:
    base = {
        "summary": "Nice place.",
        "strengths": [],
        "risks": [],
        "price_verdict": PriceVerdict.FAIR,
        "price_explanation": "",
    }
    base.update(overrides)
    return AnalysisResult(**base)


def _dated_price_payload() -> dict:
    """Minimal tri_angle response for a dated stay (5 nights)."""
    return {
        "name": "Beach Retreat",
        "price": {
            "qualifier": "for 5 nights",
            "price": "",
            "discountedPrice": "$652.45",
            "breakDown": {
                "basePrice": {
                    "description": "5 nights x $130.49",
                    "price": "$652.45",
                },
                "total": {"price": "$652.45"},
            },
        },
        "currency": "USD",
    }


# ---------------------------------------------------------------------------
# _build_actor_input — canonical URL stripping
# ---------------------------------------------------------------------------


class TestBuildActorInputCanonicalUrl:
    _ACTOR = "tri_angle~airbnb-rooms-urls-scraper"

    def test_dated_url_sends_canonical_in_start_urls(self):
        url = "https://www.airbnb.com/rooms/12345?check_in=2026-04-13&check_out=2026-04-18"
        payload = _build_actor_input(url, self._ACTOR)
        assert payload["startUrls"][0]["url"] == "https://www.airbnb.com/rooms/12345"

    def test_undated_url_unchanged_in_start_urls(self):
        url = "https://www.airbnb.com/rooms/12345"
        payload = _build_actor_input(url, self._ACTOR)
        assert payload["startUrls"][0]["url"] == url

    def test_dated_url_forwards_check_in_check_out(self):
        url = "https://www.airbnb.com/rooms/12345?check_in=2026-04-13&check_out=2026-04-18"
        payload = _build_actor_input(url, self._ACTOR)
        assert payload["checkIn"] == "2026-04-13"
        assert payload["checkOut"] == "2026-04-18"

    def test_dated_url_without_dates_no_check_in_check_out_keys(self):
        url = "https://www.airbnb.com/rooms/12345"
        payload = _build_actor_input(url, self._ACTOR)
        assert "checkIn" not in payload
        assert "checkOut" not in payload

    def test_occupancy_adults_forwarded_as_int(self):
        url = "https://www.airbnb.com/rooms/12345?check_in=2026-04-13&check_out=2026-04-18&adults=2"
        payload = _build_actor_input(url, self._ACTOR)
        assert payload["adults"] == 2

    def test_occupancy_children_forwarded(self):
        url = "https://www.airbnb.com/rooms/12345?adults=2&children=1&infants=0"
        payload = _build_actor_input(url, self._ACTOR)
        assert payload["children"] == 1
        assert payload["infants"] == 0

    def test_occupancy_pets_forwarded(self):
        url = "https://www.airbnb.com/rooms/12345?adults=2&pets=1"
        payload = _build_actor_input(url, self._ACTOR)
        assert payload["pets"] == 1

    def test_missing_occupancy_not_in_payload(self):
        url = "https://www.airbnb.com/rooms/12345"
        payload = _build_actor_input(url, self._ACTOR)
        assert "adults" not in payload
        assert "children" not in payload
        assert "infants" not in payload
        assert "pets" not in payload

    def test_fragment_stripped_from_canonical_url(self):
        url = "https://www.airbnb.com/rooms/12345?check_in=2026-04-13#section"
        payload = _build_actor_input(url, self._ACTOR)
        assert "#" not in payload["startUrls"][0]["url"]


# ---------------------------------------------------------------------------
# _normalize — stay-level PriceInfo fields
# ---------------------------------------------------------------------------


class TestNormalizeStayPriceFields:
    _DATED_URL = "https://www.airbnb.com/rooms/12345?check_in=2026-04-13&check_out=2026-04-18"

    def test_stay_nights_parsed_from_qualifier(self):
        listing = _normalize(self._DATED_URL, _dated_price_payload())
        assert listing.price is not None
        assert listing.price.stay_nights == 5

    def test_nightly_rate_parsed_from_breakdown_description(self):
        listing = _normalize(self._DATED_URL, _dated_price_payload())
        assert listing.price is not None
        assert listing.price.nightly_rate == Decimal("130.49")

    def test_check_in_populated_from_url(self):
        listing = _normalize(self._DATED_URL, _dated_price_payload())
        assert listing.price is not None
        assert listing.price.check_in == "2026-04-13"

    def test_check_out_populated_from_url(self):
        listing = _normalize(self._DATED_URL, _dated_price_payload())
        assert listing.price is not None
        assert listing.price.check_out == "2026-04-18"

    def test_total_amount_correct(self):
        listing = _normalize(self._DATED_URL, _dated_price_payload())
        assert listing.price is not None
        assert listing.price.amount == Decimal("652.45")
        assert listing.price.period == "stay"

    def test_undated_url_no_stay_fields(self):
        url = "https://www.airbnb.com/rooms/12345"
        payload = {
            "name": "Test",
            "price": {"qualifier": "night", "price": "$120", "discountedPrice": "$120"},
            "currency": "USD",
        }
        listing = _normalize(url, payload)
        assert listing.price is not None
        assert listing.price.period == "night"
        assert listing.price.check_in is None
        assert listing.price.check_out is None
        assert listing.price.stay_nights is None
        assert listing.price.nightly_rate is None

    def test_stay_nights_none_when_qualifier_has_no_number(self):
        url = "https://www.airbnb.com/rooms/12345?check_in=2026-04-13&check_out=2026-04-18"
        payload = {
            "name": "Test",
            "price": {"qualifier": "special rate", "discountedPrice": "$500"},
            "currency": "USD",
        }
        listing = _normalize(url, payload)
        assert listing.price is not None
        assert listing.price.stay_nights is None

    def test_nightly_rate_none_when_breakdown_absent(self):
        url = "https://www.airbnb.com/rooms/12345?check_in=2026-04-13&check_out=2026-04-18"
        payload = {
            "name": "Test",
            "price": {"qualifier": "for 5 nights", "discountedPrice": "$600"},
            "currency": "USD",
        }
        listing = _normalize(url, payload)
        assert listing.price is not None
        assert listing.price.nightly_rate is None


# ---------------------------------------------------------------------------
# build_prompt — stay-level context
# ---------------------------------------------------------------------------


class TestBuildPromptStayContext:
    def _stay_price(self, **overrides) -> PriceInfo:
        base = dict(
            amount=Decimal("652.45"),
            currency="USD",
            period="stay",
            check_in="2026-04-13",
            check_out="2026-04-18",
            stay_nights=5,
            nightly_rate=Decimal("130.49"),
        )
        base.update(overrides)
        return PriceInfo(**base)

    def test_stay_total_and_dates_in_prompt(self):
        listing = _listing(price=self._stay_price())
        prompt = build_prompt(listing)
        assert "652.45 USD total for stay" in prompt
        assert "2026-04-13 to 2026-04-18" in prompt

    def test_nightly_rate_in_prompt(self):
        listing = _listing(price=self._stay_price())
        prompt = build_prompt(listing)
        assert "Nightly rate: 130.49 USD" in prompt

    def test_stay_nights_count_in_prompt(self):
        listing = _listing(price=self._stay_price())
        prompt = build_prompt(listing)
        assert "5 nights" in prompt

    def test_undated_nightly_price_uses_per_period_format(self):
        listing = _listing(price=PriceInfo(amount=Decimal("120"), currency="USD", period="night"))
        prompt = build_prompt(listing)
        assert "120 USD per night" in prompt
        assert "total for stay" not in prompt

    def test_stay_without_dates_still_shows_stay_total(self):
        # stay_nights present but no check_in/check_out
        price = PriceInfo(amount=Decimal("500"), currency="USD", period="stay", stay_nights=4)
        listing = _listing(price=price)
        prompt = build_prompt(listing)
        assert "500 USD total for stay" in prompt
        assert "4 nights" in prompt


# ---------------------------------------------------------------------------
# format_analysis_message — stay-price block
# ---------------------------------------------------------------------------


class TestFormatterStayPriceBlock:
    def _stay_listing(self, **price_overrides) -> NormalizedListing:
        defaults = dict(
            amount=Decimal("652.45"),
            currency="USD",
            period="stay",
            check_in="2026-04-13",
            check_out="2026-04-18",
            stay_nights=5,
            nightly_rate=Decimal("130.49"),
        )
        defaults.update(price_overrides)
        return _listing(price=PriceInfo(**defaults))

    def test_stay_price_label_present_ru(self):
        msg = format_analysis_message(self._stay_listing(), _result())
        assert "Стоимость проживания:" in msg

    def test_stay_price_label_present_en(self):
        msg = format_analysis_message(self._stay_listing(), _result(), Language.EN)
        assert "Stay price:" in msg

    def test_stay_price_label_present_es(self):
        msg = format_analysis_message(self._stay_listing(), _result(), Language.ES)
        assert "Precio de la estancia:" in msg

    def test_total_amount_in_stay_block(self):
        msg = format_analysis_message(self._stay_listing(), _result(), Language.EN)
        assert "652.45 USD" in msg

    def test_check_in_check_out_in_stay_block(self):
        msg = format_analysis_message(self._stay_listing(), _result(), Language.EN)
        assert "2026-04-13 → 2026-04-18" in msg

    def test_nights_count_in_stay_block(self):
        msg = format_analysis_message(self._stay_listing(), _result(), Language.EN)
        assert "Nights: 5" in msg

    def test_nightly_rate_in_stay_block(self):
        msg = format_analysis_message(self._stay_listing(), _result(), Language.EN)
        assert "Per night: 130.49 USD" in msg

    def test_stay_block_omitted_for_nightly_price(self):
        listing = _listing(price=PriceInfo(amount=Decimal("120"), currency="USD", period="night"))
        msg = format_analysis_message(listing, _result(), Language.EN)
        assert "Stay price:" not in msg
        assert "Стоимость проживания:" not in msg

    def test_stay_block_omitted_when_no_price(self):
        listing = _listing()
        msg = format_analysis_message(listing, _result(), Language.EN)
        assert "Stay price:" not in msg

    def test_stay_block_omitted_when_stay_but_no_dates_or_nights(self):
        # period=stay but no check_in or stay_nights — block should be omitted
        listing = _listing(price=PriceInfo(amount=Decimal("500"), currency="USD", period="stay"))
        msg = format_analysis_message(listing, _result(), Language.EN)
        assert "Stay price:" not in msg

    def test_stay_block_without_nightly_rate_still_renders(self):
        # nightly_rate not populated — block still shows total and dates
        listing = _listing(
            price=PriceInfo(
                amount=Decimal("600"),
                currency="USD",
                period="stay",
                check_in="2026-04-13",
                check_out="2026-04-18",
                stay_nights=5,
            )
        )
        msg = format_analysis_message(listing, _result(), Language.EN)
        assert "Stay price:" in msg
        assert "600 USD" in msg
        assert "Per night:" not in msg
