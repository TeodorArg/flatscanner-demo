"""URL extraction and Telegram message routing logic."""

import re
from urllib.parse import urlparse
from typing import Literal, TypedDict

from src.telegram.models import TelegramUpdate

_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)

# Matches any Airbnb host across all localized domains, e.g.:
#   airbnb.com, www.airbnb.com, airbnb.co.uk, www.airbnb.co.uk,
#   airbnb.com.au, airbnb.de, fr.airbnb.com
# The TLD portion is restricted to:
#   - a single word (com, de, fr, …) OR
#   - a compound ccTLD in the form co.<cc> or com.<cc>
# This prevents subdomain-based look-alikes like airbnb.evil.com from matching.
_AIRBNB_HOST_RE = re.compile(
    r"^(?:[\w-]+\.)*airbnb\.(?:com|[a-z]{2}|(?:co|com)\.[a-z]{2})$",
    re.IGNORECASE,
)

# Requires exactly /rooms/<id> with an optional trailing slash — rejects bare /rooms/
# and any extra path segments like /rooms/123/photos.
_AIRBNB_LISTING_PATH_RE = re.compile(r"^/rooms/[^/?#\s]+/?$", re.IGNORECASE)


def extract_url(text: str) -> str | None:
    """Return the first HTTP/HTTPS URL found in *text*, or None."""
    match = _URL_RE.search(text)
    return match.group(0).rstrip(".,;)>") if match else None


def extract_urls(text: str) -> list[str]:
    """Return all HTTP/HTTPS URLs found in *text* (trailing punctuation stripped)."""
    return [m.rstrip(".,;)>") for m in _URL_RE.findall(text)]


def is_supported_provider(url: str) -> bool:
    """Return True if *url* is a supported Airbnb listing URL.

    Recognised patterns:
    - airbnb.com/rooms/<id> and *.airbnb.com/rooms/<id>  (listing pages only)
    - Localized Airbnb domains, e.g. airbnb.co.uk/rooms/<id>, www.airbnb.de/rooms/<id>
    - abnb.me/<code> and *.abnb.me/<code>  (Airbnb short/share links — always listings)

    Non-listing Airbnb pages (help, search, profiles, etc.) are not supported.
    """
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        path = parsed.path
    except Exception:
        return False

    if host == "abnb.me" or host.endswith(".abnb.me"):
        # Require a non-empty path segment (bare abnb.me/ with no code is not a listing)
        return bool(path) and path != "/"

    if _AIRBNB_HOST_RE.match(host):
        return bool(_AIRBNB_LISTING_PATH_RE.match(path))

    return False


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
    - ``unsupported``: message contains URLs but none from a supported provider.
    - ``help``: message has text but no URL — send usage guidance.

    All URLs in the message are inspected; a supported URL is chosen even when it
    is not the first URL in the text.
    """
    if not update.message:
        return IgnoreDecision(action="ignore")

    # Accept text from the message body or from a media caption (photo/video with URL)
    text = update.message.text or update.message.caption or ""
    if not text:
        return IgnoreDecision(action="ignore")

    urls = extract_urls(text)
    chat_id = update.message.chat.id

    if not urls:
        return HelpDecision(action="help", chat_id=chat_id)

    for url in urls:
        if is_supported_provider(url):
            return AnalyseDecision(action="analyse", url=url, chat_id=chat_id)

    # No supported URL found — report the first URL as unsupported
    return UnsupportedDecision(action="unsupported", url=urls[0], chat_id=chat_id)
