"""FastAPI router for Telegram webhook ingress."""

import logging

import httpx
from fastapi import APIRouter, HTTPException, Request

from src.domain.listing import AnalysisJob
from src.jobs.queue import enqueue_analysis_job
from src.telegram.dispatcher import route_update
from src.telegram.models import TelegramUpdate
from src.telegram.sender import send_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])

_MSG_ANALYSING = (
    "Got it! I'm looking at the listing at {url} — I'll get back to you shortly."
)
_MSG_UNSUPPORTED = (
    "Sorry, I don't support that listing provider yet. Please send an Airbnb link."
)
_MSG_HELP = (
    "Please send a rental listing URL (e.g. an Airbnb link) and I'll analyse it for you."
)


@router.post("/webhook")
async def webhook(request: Request) -> dict:
    """Receive a Telegram update and route it to the appropriate handler.

    Returns ``{"ok": true}`` in all cases so Telegram stops retrying.

    If ``Settings.telegram_webhook_secret`` is set the request must carry a
    matching ``X-Telegram-Bot-Api-Secret-Token`` header.  The secret is
    validated **before** the request body is parsed so unauthenticated
    requests are always rejected with 403 regardless of payload shape.
    """
    settings = request.app.state.settings

    if settings.telegram_webhook_secret:
        incoming_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if incoming_secret != settings.telegram_webhook_secret:
            raise HTTPException(status_code=403, detail="Forbidden")

    try:
        body = await request.json()
        update = TelegramUpdate.model_validate(body)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid update payload")

    decision = route_update(update)

    if decision["action"] == "ignore":
        return {"ok": True}

    if decision["action"] == "analyse":
        assert update.message is not None, "message must be present when action is 'analyse'"
        redis = request.app.state.redis
        if redis is not None:
            job = AnalysisJob(
                source_url=decision["url"],
                provider=decision["provider"],
                telegram_chat_id=decision["chat_id"],
                telegram_message_id=update.message.message_id,
            )
            await enqueue_analysis_job(redis, job)
        else:
            logger.warning(
                "Redis unavailable; skipping enqueue for chat_id=%s message_id=%s",
                decision["chat_id"],
                update.message.message_id,
            )
        text = _MSG_ANALYSING.format(url=decision["url"])
    elif decision["action"] == "unsupported":
        text = _MSG_UNSUPPORTED
    else:
        text = _MSG_HELP

    try:
        await send_message(settings.telegram_bot_token, decision["chat_id"], text)
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 429 or status >= 500:
            # 429 Too Many Requests and 5xx are transient — signal Telegram to retry.
            logger.exception(
                "send_message transient failure (status=%s) for chat_id=%s",
                status,
                decision["chat_id"],
            )
            raise HTTPException(status_code=502, detail="Failed to deliver reply to Telegram")
        # Other 4xx failures are permanent (e.g. bad token, blocked chat): acknowledge
        # to avoid retry loops since Telegram won't help by retrying.
        logger.error(
            "send_message permanent failure (status=%s) for chat_id=%s: %s",
            status,
            decision["chat_id"],
            exc,
        )
        return {"ok": True}
    except Exception:
        # Network / timeout / unexpected errors — transient; let Telegram retry.
        logger.exception("send_message failed for chat_id=%s", decision["chat_id"])
        raise HTTPException(status_code=502, detail="Failed to deliver reply to Telegram")
    return {"ok": True}
