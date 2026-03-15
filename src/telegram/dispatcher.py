"""URL extraction and Telegram message routing logic."""

import re
from urllib.parse import urlparse
from typing import Literal, TypedDict

from src.telegram.models import TelegramUpdate

_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)


def extract_url(text: str) -> str | None:
    """Return the first HTTP/HTTPS URL found in *text*, or None."""
    match = _URL_RE.search(text)
    return match.group(0).rstrip(".,;)>") if match else None


def is_supported_provider(url: str) -> bool:
    """Return True if *url* belongs to a supported listing provider (Airbnb).

    Recognised Airbnb hostnames:
    - airbnb.com / *.airbnb.com
    - abnb.me / *.abnb.me  (Airbnb short/share links)
    """
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return False
    return (
        host == "airbnb.com"
        or host.endswith(".airbnb.com")
        or host == "abnb.me"
        or host.endswith(".abnb.me")
    )


class IgnoreDecision(TypedDict):
    action: Literal["ignore"]


class AnalyseDecision(TypedDict):
    action: Literal["analyse"]
    url: str
    chat_id: int


class HelpDecision(TypedDict):
    action: Literal["help"]
    chat_id: int


class UnsupportedDecision(TypedDict):
    action: Literal["unsupported"]
    url: str
    chat_id: int


RoutingDecision = IgnoreDecision | AnalyseDecision | HelpDecision | UnsupportedDecision


def route_update(update: TelegramUpdate) -> RoutingDecision:
    """Inspect a Telegram update and return a routing decision.

    - ``ignore``: no message or no text to act on.
    - ``analyse``: message contains a supported provider URL — enqueue an analysis job.
    - ``unsupported``: message contains a URL from an unsupported provider.
    - ``help``: message has text but no URL — send usage guidance.
    """
    if not update.message or not update.message.text:
        return IgnoreDecision(action="ignore")

    url = extract_url(update.message.text)
    chat_id = update.message.chat.id

    if url:
        if is_supported_provider(url):
            return AnalyseDecision(action="analyse", url=url, chat_id=chat_id)
        return UnsupportedDecision(action="unsupported", url=url, chat_id=chat_id)

    return HelpDecision(action="help", chat_id=chat_id)
