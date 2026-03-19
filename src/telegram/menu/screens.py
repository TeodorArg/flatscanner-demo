"""Menu screen renderers for the Telegram inline-keyboard UX.

Each public function returns a two-tuple of ``(text, reply_markup)`` ready to
pass directly to :func:`~src.telegram.sender.send_message` or
:func:`~src.telegram.sender.edit_message_text`.

``reply_markup`` is a plain ``dict`` matching the Telegram Bot API
``InlineKeyboardMarkup`` JSON shape::

    {"inline_keyboard": [[{"text": "...", "callback_data": "..."}], ...]}
"""

from __future__ import annotations

from src.i18n import Language, get_string
from src.telegram.menu.callback import build_callback

_InlineRow = list[dict]
_InlineKeyboard = list[_InlineRow]
_ReplyMarkup = dict


def _markup(keyboard: _InlineKeyboard) -> _ReplyMarkup:
    return {"inline_keyboard": keyboard}


def _btn(label: str, data: str) -> dict:
    return {"text": label, "callback_data": data}


def render_main_menu(lang: Language) -> tuple[str, _ReplyMarkup]:
    """Return the primary menu screen: language, settings, billing, and help."""
    text = get_string("menu.main.title", lang)
    keyboard: _InlineKeyboard = [
        [_btn(get_string("menu.main.lang_btn", lang), build_callback("main", "nav", "language"))],
        [_btn(get_string("menu.main.settings_btn", lang), build_callback("main", "nav", "settings"))],
        [_btn(get_string("menu.main.billing_btn", lang), build_callback("main", "nav", "billing"))],
        [_btn(get_string("menu.main.help_btn", lang), build_callback("main", "nav", "help"))],
    ]
    return text, _markup(keyboard)


def render_language_screen(lang: Language) -> tuple[str, _ReplyMarkup]:
    """Return the language-selection screen with RU / EN / ES buttons."""
    text = get_string("menu.language.title", lang)
    keyboard: _InlineKeyboard = [
        [_btn(get_string("menu.language.ru_btn", lang), build_callback("language", "set", "ru"))],
        [_btn(get_string("menu.language.en_btn", lang), build_callback("language", "set", "en"))],
        [_btn(get_string("menu.language.es_btn", lang), build_callback("language", "set", "es"))],
        [_btn(get_string("menu.back_btn", lang), build_callback("language", "back", "main"))],
    ]
    return text, _markup(keyboard)


def render_settings_screen(lang: Language) -> tuple[str, _ReplyMarkup]:
    """Return the settings stub screen (placeholder for future options)."""
    title = get_string("menu.settings.title", lang)
    body = get_string("menu.settings.body", lang)
    text = f"{title}\n\n{body}"
    keyboard: _InlineKeyboard = [
        [_btn(get_string("menu.back_btn", lang), build_callback("settings", "back", "main"))],
    ]
    return text, _markup(keyboard)


def render_billing_screen(lang: Language) -> tuple[str, _ReplyMarkup]:
    """Return the billing stub screen (placeholder for plans and checkout)."""
    title = get_string("menu.billing.title", lang)
    body = get_string("menu.billing.body", lang)
    text = f"{title}\n\n{body}"
    keyboard: _InlineKeyboard = [
        [_btn(get_string("menu.back_btn", lang), build_callback("billing", "back", "main"))],
    ]
    return text, _markup(keyboard)


def render_help_screen(lang: Language) -> tuple[str, _ReplyMarkup]:
    """Return the help screen with a back button to the main menu."""
    title = get_string("menu.help.title", lang)
    body = get_string("menu.help.body", lang)
    text = f"{title}\n\n{body}"
    keyboard: _InlineKeyboard = [
        [_btn(get_string("menu.back_btn", lang), build_callback("help", "back", "main"))],
    ]
    return text, _markup(keyboard)


# Map screen name → renderer for use in the router callback dispatcher.
SCREEN_RENDERERS: dict[str, callable] = {
    "main": render_main_menu,
    "language": render_language_screen,
    "settings": render_settings_screen,
    "billing": render_billing_screen,
    "help": render_help_screen,
}
