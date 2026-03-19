"""Telegram Bot API BotCommand definitions with localized descriptions.

Command names are always English. Only descriptions are localized.
Use :func:`get_bot_commands` to obtain the payload list for ``setMyCommands``.
"""

from __future__ import annotations

from src.i18n.types import DEFAULT_LANGUAGE, Language

# Ordered list of commands as they appear in the Telegram command picker.
COMMAND_ORDER: list[str] = ["menu", "language", "settings", "billing", "help"]

# Localized descriptions for each command. Every command must have an entry
# for DEFAULT_LANGUAGE (Russian); other languages fall back to Russian.
_DESCRIPTIONS: dict[str, dict[Language, str]] = {
    "menu": {
        Language.RU: "\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u0433\u043b\u0430\u0432\u043d\u043e\u0435 \u043c\u0435\u043d\u044e",
        Language.EN: "Open the main menu",
        Language.ES: "Abrir el men\u00fa principal",
    },
    "language": {
        Language.RU: "\u0421\u043c\u0435\u043d\u0438\u0442\u044c \u044f\u0437\u044b\u043a",
        Language.EN: "Change language",
        Language.ES: "Cambiar idioma",
    },
    "settings": {
        Language.RU: "\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438",
        Language.EN: "Settings",
        Language.ES: "Configuraci\u00f3n",
    },
    "billing": {
        Language.RU: "\u041e\u043f\u043b\u0430\u0442\u0430 \u0438 \u0442\u0430\u0440\u0438\u0444\u044b",
        Language.EN: "Billing and plans",
        Language.ES: "Facturaci\u00f3n y planes",
    },
    "help": {
        Language.RU: "\u041f\u043e\u043c\u043e\u0449\u044c",
        Language.EN: "Help",
        Language.ES: "Ayuda",
    },
}


def get_bot_commands(lang: Language) -> list[dict]:
    """Return Telegram ``BotCommand`` dicts localized for *lang*.

    Each entry contains:
    - ``command``: always English and stable across languages
    - ``description``: localized to *lang*, falling back to Russian
    """
    result = []
    for name in COMMAND_ORDER:
        descriptions = _DESCRIPTIONS[name]
        description = descriptions.get(lang) or descriptions[DEFAULT_LANGUAGE]
        result.append({"command": name, "description": description})
    return result
