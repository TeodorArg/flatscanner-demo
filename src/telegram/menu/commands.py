"""Telegram Bot API BotCommand definitions with localized descriptions.

Command names are always English (Telegram requirement).  Only descriptions
are localized.  Use :func:`get_bot_commands` to obtain the payload list for
``setMyCommands``.
"""

from __future__ import annotations

from src.i18n.types import DEFAULT_LANGUAGE, Language

# Ordered list of commands as they appear in the Telegram command picker.
COMMAND_ORDER: list[str] = ["menu", "language", "settings", "billing", "help"]

# Localized descriptions for each command.  Every command MUST have an entry
# for DEFAULT_LANGUAGE (Russian); other languages fall back to Russian.
_DESCRIPTIONS: dict[str, dict[Language, str]] = {
    "menu": {
        Language.RU: "Открыть главное меню",
        Language.EN: "Open the main menu",
        Language.ES: "Abrir el menú principal",
    },
    "language": {
        Language.RU: "Сменить язык",
        Language.EN: "Change language",
        Language.ES: "Cambiar idioma",
    },
    "settings": {
        Language.RU: "Настройки",
        Language.EN: "Settings",
        Language.ES: "Configuración",
    },
    "billing": {
        Language.RU: "Оплата и тарифы",
        Language.EN: "Billing and plans",
        Language.ES: "Facturación y planes",
    },
    "help": {
        Language.RU: "Помощь",
        Language.EN: "Help",
        Language.ES: "Ayuda",
    },
}


def get_bot_commands(lang: Language) -> list[dict]:
    """Return the list of BotCommand dicts for the Telegram ``setMyCommands`` API.

    Each entry has ``command`` (always English) and ``description`` (localized
    to *lang*, falling back to Russian if no entry exists).

    Parameters
    ----------
    lang:
        Desired description language.
    """
    result = []
    for name in COMMAND_ORDER:
        descriptions = _DESCRIPTIONS[name]
        description = descriptions.get(lang) or descriptions[DEFAULT_LANGUAGE]
        result.append({"command": name, "description": description})
    return result
