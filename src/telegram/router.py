"""FastAPI router for Telegram webhook ingress."""

import logging

import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException, Request

from src.domain.listing import AnalysisJob
from src.i18n import DEFAULT_LANGUAGE, get_string
from src.jobs.queue import enqueue_analysis_job
from src.storage.chat_preferences import get_chat_language, set_chat_language
from src.telegram.dispatcher import route_update
from src.telegram.models import TelegramUpdate
from src.telegram.sender import send_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


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

    # Determine the effective language for this chat.  Best-effort: if Redis is
    # not yet available (e.g. during startup) we fall back to the default
    # language so non-analyse paths can still reply.
    redis = request.app.state.redis
    if redis is not None:
        lang = await get_chat_language(redis, decision["chat_id"])
    else:
        lang = DEFAULT_LANGUAGE

    if decision["action"] == "analyse":
        if update.message is None:
            # Defensive: route_update only returns 'analyse' when a message is present.
            # Guard explicitly rather than relying on assert (disabled under -O).
            logger.error(
                "route_update returned 'analyse' but update.message is None; dropping update"
            )
            return {"ok": True}
        if redis is None:
            logger.warning(
                "Redis unavailable; cannot enqueue job for chat_id=%s — returning 502 for retry",
                decision["chat_id"],
            )
            raise HTTPException(status_code=502, detail="Queue unavailable; please retry")
        job = AnalysisJob(
            source_url=decision["url"],
            provider=decision["provider"],
            telegram_chat_id=decision["chat_id"],
            telegram_message_id=update.message.message_id,
            language=lang,
        )
        try:
            await enqueue_analysis_job(redis, job)
        except aioredis.RedisError as exc:
            logger.error(
                "Redis error while enqueueing job for chat_id=%s url=%s: %s",
                decision["chat_id"],
                decision["url"],
                exc,
            )
            raise HTTPException(status_code=502, detail="Queue unavailable; please retry")
        text = get_string("msg.analysing", lang).format(url=decision["url"])
    elif decision["action"] == "set_language":
        target_lang = decision["language"]
        if target_lang is None:
            # Unrecognised or missing language code — reply in the current chat language.
            text = get_string("msg.language_invalid", lang)
        else:
            if redis is not None:
                try:
                    await set_chat_language(redis, decision["chat_id"], target_lang)
                except aioredis.RedisError as exc:
                    logger.error(
                        "Redis error while saving language for chat_id=%s: %s",
                        decision["chat_id"],
                        exc,
                    )
                    raise HTTPException(status_code=502, detail="Queue unavailable; please retry")
            # Confirm in the new language so the user sees immediate feedback.
            text = get_string("msg.language_set", target_lang)
    elif decision["action"] == "unsupported":
        text = get_string("msg.unsupported", lang)
    else:
        text = get_string("msg.help", lang)

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
