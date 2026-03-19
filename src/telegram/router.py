"""FastAPI router for Telegram webhook ingress."""

import logging

import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException, Request

from src.domain.listing import AnalysisJob
from src.i18n import DEFAULT_LANGUAGE, Language, get_string
from src.jobs.queue import enqueue_analysis_job
from src.storage.chat_preferences import get_chat_language, set_chat_language
from src.storage.chat_settings import ChatSettings, get_chat_settings, save_chat_settings
from src.telegram.dispatcher import route_update
from src.telegram.menu.callback import parse_callback
from src.telegram.menu.screens import SCREEN_RENDERERS, render_language_screen, render_main_menu
from src.telegram.models import TelegramUpdate
from src.telegram.sender import answer_callback_query, edit_message_text, send_message

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
    app_settings = request.app.state.settings

    if app_settings.telegram_webhook_secret:
        incoming_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if incoming_secret != app_settings.telegram_webhook_secret:
            raise HTTPException(status_code=403, detail="Forbidden")

    try:
        body = await request.json()
        update = TelegramUpdate.model_validate(body)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid update payload")

    decision = route_update(update)

    if decision["action"] == "ignore":
        return {"ok": True}

    token = app_settings.telegram_bot_token

    # -----------------------------------------------------------------------
    # Menu callback: inline-keyboard button press
    # -----------------------------------------------------------------------
    if decision["action"] == "menu_callback":
        redis = request.app.state.redis
        parsed = parse_callback(decision["callback_data"])

        if parsed is None:
            # Unrecognised payload — dismiss the spinner silently.
            await _safe_answer_callback(token, decision["callback_query_id"])
            return {"ok": True}

        if parsed.action in ("nav", "back"):
            renderer = SCREEN_RENDERERS.get(parsed.value)
            if renderer is None:
                await _safe_answer_callback(token, decision["callback_query_id"])
                return {"ok": True}
            if redis is None:
                logger.warning(
                    "Redis unavailable; cannot load settings for callback chat_id=%s",
                    decision["chat_id"],
                )
                raise HTTPException(status_code=502, detail="Storage unavailable; please retry")
            try:
                chat_settings = await get_chat_settings(redis, decision["chat_id"])
            except aioredis.RedisError as exc:
                logger.error(
                    "Redis error while loading settings for nav callback chat_id=%s: %s",
                    decision["chat_id"],
                    exc,
                )
                raise HTTPException(status_code=502, detail="Storage unavailable; please retry")
            text, markup = renderer(chat_settings.language)
            await _safe_answer_callback(token, decision["callback_query_id"])
            await _safe_edit_message(
                token, decision["chat_id"], decision["message_id"], text, markup
            )
            return {"ok": True}

        if parsed.action == "set" and parsed.screen == "language":
            try:
                new_lang = Language(parsed.value)
            except ValueError:
                await _safe_answer_callback(token, decision["callback_query_id"])
                return {"ok": True}
            if redis is None:
                logger.warning(
                    "Redis unavailable; cannot save language for callback chat_id=%s",
                    decision["chat_id"],
                )
                raise HTTPException(status_code=502, detail="Storage unavailable; please retry")
            try:
                current = await get_chat_settings(redis, decision["chat_id"])
                updated = current.model_copy(update={"language": new_lang})
                await save_chat_settings(redis, decision["chat_id"], updated)
            except aioredis.RedisError as exc:
                logger.error(
                    "Redis error while saving language via menu for chat_id=%s: %s",
                    decision["chat_id"],
                    exc,
                )
                raise HTTPException(
                    status_code=502, detail="Could not save language preference; please retry"
                )
            confirm_text = get_string("menu.language.selected", new_lang)
            lang_text, lang_markup = render_language_screen(new_lang)
            await _safe_answer_callback(
                token, decision["callback_query_id"], text=confirm_text
            )
            await _safe_edit_message(
                token, decision["chat_id"], decision["message_id"], lang_text, lang_markup
            )
            return {"ok": True}

        # Unhandled action type — dismiss spinner silently.
        await _safe_answer_callback(token, decision["callback_query_id"])
        return {"ok": True}

    # -----------------------------------------------------------------------
    # /menu command — handled before language loading since it uses
    # get_chat_settings directly.
    # -----------------------------------------------------------------------
    if decision["action"] == "open_menu":
        redis = request.app.state.redis
        if redis is None:
            logger.warning(
                "Redis unavailable; cannot load settings for /menu chat_id=%s",
                decision["chat_id"],
            )
            raise HTTPException(status_code=502, detail="Storage unavailable; please retry")
        try:
            chat_settings = await get_chat_settings(redis, decision["chat_id"])
        except aioredis.RedisError as exc:
            logger.error(
                "Redis error while loading settings for /menu chat_id=%s: %s",
                decision["chat_id"],
                exc,
            )
            raise HTTPException(status_code=502, detail="Storage unavailable; please retry")
        text, markup = render_main_menu(chat_settings.language)
        try:
            await send_message(token, decision["chat_id"], text, reply_markup=markup)
        except httpx.HTTPStatusError as exc:
            return _handle_send_error(exc, decision["chat_id"])
        except Exception:
            logger.exception("send_message failed for chat_id=%s", decision["chat_id"])
            raise HTTPException(status_code=502, detail="Failed to deliver reply to Telegram")
        return {"ok": True}

    # -----------------------------------------------------------------------
    # Determine the effective language for this chat.  Best-effort: if Redis
    # is not yet available (e.g. during startup) we fall back to the default
    # language so non-analyse paths can still reply.
    # -----------------------------------------------------------------------
    redis = request.app.state.redis
    if redis is not None:
        lang = await get_chat_language(redis, decision["chat_id"])
    else:
        lang = DEFAULT_LANGUAGE

    # -----------------------------------------------------------------------
    # Analyse
    # -----------------------------------------------------------------------
    if decision["action"] == "analyse":
        if update.message is None:
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

    # -----------------------------------------------------------------------
    # /language command
    # -----------------------------------------------------------------------
    elif decision["action"] == "set_language":
        target_lang = decision["language"]
        if target_lang is None:
            text = get_string("msg.language_invalid", lang)
        else:
            if redis is None:
                logger.warning(
                    "Redis unavailable; cannot save language for chat_id=%s",
                    decision["chat_id"],
                )
                raise HTTPException(
                    status_code=502,
                    detail="Language preference storage unavailable; please retry",
                )
            try:
                await set_chat_language(redis, decision["chat_id"], target_lang)
            except aioredis.RedisError as exc:
                logger.error(
                    "Redis error while saving language for chat_id=%s: %s",
                    decision["chat_id"],
                    exc,
                )
                raise HTTPException(
                    status_code=502,
                    detail="Could not save language preference; please retry",
                )
            text = get_string("msg.language_set", target_lang)

    elif decision["action"] == "unsupported":
        text = get_string("msg.unsupported", lang)

    else:
        text = get_string("msg.help", lang)

    try:
        await send_message(token, decision["chat_id"], text)
    except httpx.HTTPStatusError as exc:
        return _handle_send_error(exc, decision["chat_id"])
    except Exception:
        logger.exception("send_message failed for chat_id=%s", decision["chat_id"])
        raise HTTPException(status_code=502, detail="Failed to deliver reply to Telegram")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _handle_send_error(exc: httpx.HTTPStatusError, chat_id: int) -> dict:
    status = exc.response.status_code
    if status == 429 or status >= 500:
        logger.exception(
            "send_message transient failure (status=%s) for chat_id=%s",
            status,
            chat_id,
        )
        raise HTTPException(status_code=502, detail="Failed to deliver reply to Telegram")
    logger.error(
        "send_message permanent failure (status=%s) for chat_id=%s: %s",
        status,
        chat_id,
        exc,
    )
    return {"ok": True}


async def _safe_answer_callback(
    token: str,
    callback_query_id: str,
    *,
    text: str | None = None,
) -> None:
    """Answer a callback query, swallowing permanent Telegram errors."""
    try:
        await answer_callback_query(token, callback_query_id, text=text)
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 429 or status >= 500:
            logger.exception(
                "answer_callback_query transient failure (status=%s) cbq_id=%s",
                status,
                callback_query_id,
            )
            raise HTTPException(status_code=502, detail="Failed to answer callback query")
        logger.error(
            "answer_callback_query permanent failure (status=%s) cbq_id=%s: %s",
            status,
            callback_query_id,
            exc,
        )
    except Exception:
        logger.exception("answer_callback_query failed cbq_id=%s", callback_query_id)
        raise HTTPException(status_code=502, detail="Failed to answer callback query")


async def _safe_edit_message(
    token: str,
    chat_id: int,
    message_id: int,
    text: str,
    reply_markup: dict | None = None,
) -> None:
    """Edit a message, swallowing permanent Telegram errors (e.g. message not modified)."""
    try:
        await edit_message_text(
            token, chat_id, message_id, text, reply_markup=reply_markup
        )
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        if status == 429 or status >= 500:
            logger.exception(
                "edit_message_text transient failure (status=%s) for chat_id=%s",
                status,
                chat_id,
            )
            raise HTTPException(status_code=502, detail="Failed to edit menu message")
        # 400 "message is not modified" and other 4xx are permanent — ignore.
        logger.error(
            "edit_message_text permanent failure (status=%s) for chat_id=%s: %s",
            status,
            chat_id,
            exc,
        )
    except Exception:
        logger.exception("edit_message_text failed for chat_id=%s", chat_id)
        raise HTTPException(status_code=502, detail="Failed to edit menu message")
