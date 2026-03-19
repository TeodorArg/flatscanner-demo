"""URL extraction and Telegram message routing logic."""

import re
from typing import Literal, TypedDict

from src.adapters.registry import detect_provider
from src.domain.listing import ListingProvider
from src.i18n.types import Language
from src.telegram.menu.callback import is_menu_callback
from src.telegram.models import TelegramUpdate

_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)

# Matches "/language" optionally followed by a language code, e.g. "/language ru".
_LANGUAGE_CMD_RE = re.compile(r"^/language(?:\s+(\S+))?", re.IGNORECASE)

# Matches "/menu" with optional trailing whitespace.
_MENU_CMD_RE = re.compile(r"^/menu\b", re.IGNORECASE)

# Matches command entry points that open specific menu screens directly.
_SETTINGS_CMD_RE = re.compile(r"^/settings\b", re.IGNORECASE)
_BILLING_CMD_RE = re.compile(r"^/billing\b", re.IGNORECASE)
_HELP_CMD_RE = re.compile(r"^/help\b", re.IGNORECASE)


def extract_url(text: str) -> str | None:
    """Return the first HTTP/HTTPS URL found in *text*, or None."""
    match = _URL_RE.search(text)
    return match.group(0).rstrip(".,;)>") if match else None


def extract_urls(text: str) -> list[str]:
    """Return all HTTP/HTTPS URLs found in *text* (trailing punctuation stripped)."""
    return [m.rstrip(".,;)>") for m in _URL_RE.findall(text)]


def is_supported_provider(url: str) -> bool:
    """Return True if *url* belongs to a supported listing provider.

    Delegates to the adapter registry so this module stays provider-agnostic.
    See ``src/adapters/`` for per-provider URL recognition rules.
    """
    return detect_provider(url) != ListingProvider.UNKNOWN


class IgnoreDecision(TypedDict):
    action: Literal["ignore"]


class AnalyseDecision(TypedDict):
    action: Literal["analyse"]
    url: str
    chat_id: int
    provider: ListingProvider


class HelpDecision(TypedDict):
    action: Literal["help"]
    chat_id: int


class UnsupportedDecision(TypedDict):
    action: Literal["unsupported"]
    url: str
    chat_id: int


class SetLanguageDecision(TypedDict):
    action: Literal["set_language"]
    chat_id: int
    # None means the user provided an unrecognised or missing language code.
    language: Language | None


class OpenMenuDecision(TypedDict):
    action: Literal["open_menu"]
    chat_id: int


class OpenScreenDecision(TypedDict):
    action: Literal["open_screen"]
    chat_id: int
    screen: Literal["settings", "billing", "help"]


class MenuCallbackDecision(TypedDict):
    action: Literal["menu_callback"]
    chat_id: int
    callback_query_id: str
    message_id: int
    callback_data: str


RoutingDecision = (
    IgnoreDecision
    | AnalyseDecision
    | HelpDecision
    | UnsupportedDecision
    | SetLanguageDecision
    | OpenMenuDecision
    | OpenScreenDecision
    | MenuCallbackDecision
)


def route_update(update: TelegramUpdate) -> RoutingDecision:
    """Inspect a Telegram update and return a routing decision.

    - ``ignore``: no actionable content.
    - ``open_menu``: user sent the ``/menu`` command.
    - ``menu_callback``: user pressed an inline-keyboard button with menu data.
    - ``analyse``: message contains a supported provider URL.
    - ``unsupported``: message contains URLs but none from a supported provider.
    - ``set_language``: message is a ``/language <code>`` command.
    - ``help``: message has text but no URL and no recognised command.
    """
    # --- Callback queries (inline keyboard button presses) ---
    if update.callback_query is not None:
        cb = update.callback_query
        if cb.data and is_menu_callback(cb.data) and cb.message is not None:
            return MenuCallbackDecision(
                action="menu_callback",
                chat_id=cb.message.chat.id,
                callback_query_id=cb.id,
                message_id=cb.message.message_id,
                callback_data=cb.data,
            )
        return IgnoreDecision(action="ignore")

    # --- Regular messages ---
    if not update.message:
        return IgnoreDecision(action="ignore")

    # Accept text from the message body or from a media caption (photo/video with URL)
    text = update.message.text or update.message.caption or ""
    if not text:
        return IgnoreDecision(action="ignore")

    urls = extract_urls(text)
    chat_id = update.message.chat.id

    if not urls:
        stripped = text.strip()
        # /menu command
        if _MENU_CMD_RE.match(stripped):
            return OpenMenuDecision(action="open_menu", chat_id=chat_id)
        # /settings, /billing, /help — open the corresponding menu screen directly
        if _SETTINGS_CMD_RE.match(stripped):
            return OpenScreenDecision(action="open_screen", chat_id=chat_id, screen="settings")
        if _BILLING_CMD_RE.match(stripped):
            return OpenScreenDecision(action="open_screen", chat_id=chat_id, screen="billing")
        if _HELP_CMD_RE.match(stripped):
            return OpenScreenDecision(action="open_screen", chat_id=chat_id, screen="help")
        # /language command
        m = _LANGUAGE_CMD_RE.match(stripped)
        if m:
            code = m.group(1)
            lang: Language | None = None
            if code is not None:
                try:
                    lang = Language(code.lower())
                except ValueError:
                    lang = None
            return SetLanguageDecision(action="set_language", chat_id=chat_id, language=lang)
        return HelpDecision(action="help", chat_id=chat_id)

    for url in urls:
        provider = detect_provider(url)
        if provider != ListingProvider.UNKNOWN:
            return AnalyseDecision(
                action="analyse", url=url, chat_id=chat_id, provider=provider
            )

    # No supported URL found — report the first URL as unsupported
    return UnsupportedDecision(action="unsupported", url=urls[0], chat_id=chat_id)
