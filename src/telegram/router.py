"""FastAPI router for Telegram webhook ingress."""

import logging

from fastapi import APIRouter, Request

from src.telegram.dispatcher import route_update
from src.telegram.models import TelegramUpdate
from src.telegram.sender import send_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])

_MSG_ANALYSING = (
    "Got it! I'm looking at the listing at {url} — I'll get back to you shortly."
)
_MSG_HELP = (
    "Please send a rental listing URL (e.g. an Airbnb link) and I'll analyse it for you."
)


@router.post("/webhook")
async def webhook(request: Request, update: TelegramUpdate) -> dict:
    """Receive a Telegram update and route it to the appropriate handler.

    Returns ``{"ok": true}`` in all cases so Telegram stops retrying.
    """
    settings = request.app.state.settings
    decision = route_update(update)

    if decision["action"] == "ignore":
        return {"ok": True}

    if decision["action"] == "analyse":
        text = _MSG_ANALYSING.format(url=decision["url"])
    else:
        text = _MSG_HELP

    try:
        await send_message(settings.telegram_bot_token, decision["chat_id"], text)
    except Exception:
        logger.exception("send_message failed for chat_id=%s", decision["chat_id"])
    return {"ok": True}
