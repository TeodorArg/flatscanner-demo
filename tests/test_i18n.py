"""Tests for the i18n catalog and Language type."""

from __future__ import annotations

import pytest

from src.i18n.catalog import get_string
from src.i18n.types import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, Language


# ---------------------------------------------------------------------------
# Language enum
# ---------------------------------------------------------------------------


class TestLanguageEnum:
    def test_enum_has_three_values(self):
        assert len(Language) == 3

    def test_values_are_iso_codes(self):
        assert Language.RU.value == "ru"
        assert Language.EN.value == "en"
        assert Language.ES.value == "es"

    def test_is_str_subclass(self):
        assert isinstance(Language.RU, str)

    def test_default_language_is_russian(self):
        assert DEFAULT_LANGUAGE == Language.RU

    def test_all_languages_in_supported_set(self):
        assert SUPPORTED_LANGUAGES == frozenset(Language)


# ---------------------------------------------------------------------------
# Catalog lookup
# ---------------------------------------------------------------------------


class TestGetString:
    def test_returns_english_string_for_en(self):
        result = get_string("msg.help", Language.EN)
        assert "Airbnb" in result
        # English text must not be the Russian text
        assert "Пожалуйста" not in result

    def test_returns_russian_string_for_ru(self):
        result = get_string("msg.help", Language.RU)
        assert "Пожалуйста" in result

    def test_returns_spanish_string_for_es(self):
        result = get_string("msg.help", Language.ES)
        assert "favor" in result

    def test_all_keys_have_russian_entry(self):
        """Every key must have a Russian entry (the fallback language)."""
        keys = ["msg.help", "msg.unsupported", "msg.analysing"]
        for key in keys:
            result = get_string(key, Language.RU)
            assert result, f"Empty Russian string for key {key!r}"

    def test_analysing_string_contains_placeholder(self):
        for lang in Language:
            result = get_string("msg.analysing", lang)
            assert "{url}" in result, f"Missing {{url}} placeholder for language {lang}"

    def test_unknown_key_raises_key_error(self):
        with pytest.raises(KeyError, match="unknown.key"):
            get_string("unknown.key", Language.RU)


# ---------------------------------------------------------------------------
# Fallback behaviour
# ---------------------------------------------------------------------------


class TestFallback:
    def test_falls_back_to_russian_when_lang_missing(self):
        """If a language has no entry, get_string falls back to DEFAULT_LANGUAGE."""
        # Directly inject a partial entry to simulate a missing translation.
        from src.i18n import catalog as _cat

        original = _cat._CATALOG.get("msg.help", {}).copy()
        partial = {Language.RU: "Тест"}
        _cat._CATALOG["msg.help"] = partial
        try:
            result = get_string("msg.help", Language.EN)
            assert result == "Тест"
        finally:
            _cat._CATALOG["msg.help"] = original

    def test_returns_requested_lang_when_present(self):
        """When the language exists, get_string must NOT fall back."""
        result_ru = get_string("msg.unsupported", Language.RU)
        result_en = get_string("msg.unsupported", Language.EN)
        assert result_ru != result_en
