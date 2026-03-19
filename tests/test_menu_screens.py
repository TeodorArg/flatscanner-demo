"""Tests for menu screen rendering."""

from __future__ import annotations

import pytest

from src.i18n.types import Language
from src.telegram.menu.callback import build_callback, is_menu_callback, parse_callback
from src.telegram.menu.screens import (
    render_billing_screen,
    render_help_screen,
    render_language_screen,
    render_main_menu,
    render_settings_screen,
)


def _buttons(markup: dict) -> list[dict]:
    """Flatten all buttons in an InlineKeyboardMarkup into a single list."""
    return [btn for row in markup["inline_keyboard"] for btn in row]


def _callback_data(markup: dict) -> list[str]:
    return [btn["callback_data"] for btn in _buttons(markup)]


class TestRenderMainMenu:
    def test_returns_text_and_markup_tuple(self):
        text, markup = render_main_menu(Language.EN)
        assert isinstance(text, str)
        assert "inline_keyboard" in markup

    @pytest.mark.parametrize("lang", list(Language))
    def test_text_is_non_empty_for_all_languages(self, lang):
        text, _ = render_main_menu(lang)
        assert text.strip()

    def test_has_four_buttons(self):
        _, markup = render_main_menu(Language.EN)
        assert len(_buttons(markup)) == 4

    def test_all_callbacks_are_menu_callbacks(self):
        _, markup = render_main_menu(Language.RU)
        for data in _callback_data(markup):
            assert is_menu_callback(data), f"{data!r} is not a menu callback"

    def test_language_button_navigates_to_language_screen(self):
        _, markup = render_main_menu(Language.EN)
        datas = _callback_data(markup)
        language_btn = next(
            (d for d in datas if parse_callback(d) and parse_callback(d).value == "language"),
            None,
        )
        assert language_btn is not None

    def test_settings_button_exists(self):
        _, markup = render_main_menu(Language.EN)
        datas = _callback_data(markup)
        assert any(
            parse_callback(d) and parse_callback(d).value == "settings" for d in datas
        )

    def test_billing_button_exists(self):
        _, markup = render_main_menu(Language.EN)
        datas = _callback_data(markup)
        assert any(
            parse_callback(d) and parse_callback(d).value == "billing" for d in datas
        )

    def test_help_button_exists(self):
        _, markup = render_main_menu(Language.EN)
        datas = _callback_data(markup)
        assert any(
            parse_callback(d) and parse_callback(d).value == "help" for d in datas
        )

    def test_russian_text_differs_from_english(self):
        ru_text, _ = render_main_menu(Language.RU)
        en_text, _ = render_main_menu(Language.EN)
        assert ru_text != en_text


class TestRenderLanguageScreen:
    def test_has_four_buttons(self):
        _, markup = render_language_screen(Language.EN)
        assert len(_buttons(markup)) == 4

    def test_three_language_set_buttons(self):
        _, markup = render_language_screen(Language.EN)
        set_buttons = [
            d for d in _callback_data(markup)
            if (cb := parse_callback(d)) and cb.action == "set"
        ]
        assert len(set_buttons) == 3

    def test_set_buttons_target_all_three_languages(self):
        _, markup = render_language_screen(Language.EN)
        values = {
            parse_callback(d).value
            for d in _callback_data(markup)
            if (cb := parse_callback(d)) and cb.action == "set"
        }
        assert values == {"ru", "en", "es"}

    def test_back_button_goes_to_main(self):
        _, markup = render_language_screen(Language.EN)
        back_btns = [
            d for d in _callback_data(markup)
            if (cb := parse_callback(d)) and cb.action == "back" and cb.value == "main"
        ]
        assert len(back_btns) == 1

    @pytest.mark.parametrize("lang", list(Language))
    def test_text_is_non_empty_for_all_languages(self, lang):
        text, _ = render_language_screen(lang)
        assert text.strip()

    def test_set_callbacks_use_language_screen(self):
        _, markup = render_language_screen(Language.EN)
        for data in _callback_data(markup):
            cb = parse_callback(data)
            assert cb is not None
            assert cb.screen == "language"


class TestRenderSettingsScreen:
    def test_has_back_button(self):
        _, markup = render_settings_screen(Language.EN)
        back_btns = [
            d for d in _callback_data(markup)
            if (cb := parse_callback(d)) and cb.action == "back" and cb.value == "main"
        ]
        assert len(back_btns) == 1

    @pytest.mark.parametrize("lang", list(Language))
    def test_text_contains_title_and_body(self, lang):
        from src.i18n import get_string

        text, _ = render_settings_screen(lang)
        assert get_string("menu.settings.title", lang) in text
        assert get_string("menu.settings.body", lang) in text

    def test_back_callback_from_settings_screen(self):
        _, markup = render_settings_screen(Language.RU)
        cb = parse_callback(_callback_data(markup)[0])
        assert cb is not None
        assert cb.screen == "settings"
        assert cb.action == "back"
        assert cb.value == "main"


class TestRenderBillingScreen:
    def test_has_back_button(self):
        _, markup = render_billing_screen(Language.EN)
        back_btns = [
            d for d in _callback_data(markup)
            if (cb := parse_callback(d)) and cb.action == "back" and cb.value == "main"
        ]
        assert len(back_btns) == 1

    @pytest.mark.parametrize("lang", list(Language))
    def test_text_contains_title_and_body(self, lang):
        from src.i18n import get_string

        text, _ = render_billing_screen(lang)
        assert get_string("menu.billing.title", lang) in text
        assert get_string("menu.billing.body", lang) in text

    def test_back_callback_from_billing_screen(self):
        _, markup = render_billing_screen(Language.ES)
        cb = parse_callback(_callback_data(markup)[0])
        assert cb is not None
        assert cb.screen == "billing"
        assert cb.action == "back"
        assert cb.value == "main"


class TestRenderHelpScreen:
    def test_has_back_button(self):
        _, markup = render_help_screen(Language.EN)
        back_btns = [
            d for d in _callback_data(markup)
            if (cb := parse_callback(d)) and cb.action == "back" and cb.value == "main"
        ]
        assert len(back_btns) == 1

    @pytest.mark.parametrize("lang", list(Language))
    def test_text_is_non_empty_for_all_languages(self, lang):
        text, _ = render_help_screen(lang)
        assert text.strip()

    def test_back_callback_from_help_screen(self):
        _, markup = render_help_screen(Language.EN)
        cb = parse_callback(_callback_data(markup)[0])
        assert cb is not None
        assert cb.screen == "help"
        assert cb.action == "back"
        assert cb.value == "main"
