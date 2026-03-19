"""Outgoing Telegram message helpers.

Sends replies via the Telegram Bot API using httpx.  An optional pre-built
``httpx.AsyncClient`` can be injected for testing without real network calls.
"""

import httpx

_BASE = "https://api.telegram.org/bot{token}"
_SEND_MESSAGE_URL = _BASE + "/sendMessage"
_EDIT_MESSAGE_URL = _BASE + "/editMessageText"
_ANSWER_CALLBACK_URL = _BASE + "/answerCallbackQuery"


async def _post(url: str, payload: dict, *, client: httpx.AsyncClient | None) -> None:
    if client is not None:
        response = await client.post(url, json=payload)
        response.raise_for_status()
    else:
        async with httpx.AsyncClient() as c:
            response = await c.post(url, json=payload)
            response.raise_for_status()


async def send_message(
    token: str,
    chat_id: int,
    text: str,
    *,
    reply_markup: dict | None = None,
    client: httpx.AsyncClient | None = None,
) -> None:
    """POST a text message to *chat_id* via the Telegram Bot API.

    Args:
        token: Telegram bot token from ``Settings.telegram_bot_token``.
        chat_id: Target chat identifier.
        text: Message body (plain text).
        reply_markup: Optional inline keyboard or other reply markup dict.
        client: Optional injected ``httpx.AsyncClient`` (for tests).
    """
    payload: dict = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    await _post(_SEND_MESSAGE_URL.format(token=token), payload, client=client)


async def edit_message_text(
    token: str,
    chat_id: int,
    message_id: int,
    text: str,
    *,
    reply_markup: dict | None = None,
    client: httpx.AsyncClient | None = None,
) -> None:
    """Edit the text of an existing message via the Telegram Bot API.

    Args:
        token: Telegram bot token.
        chat_id: Chat that owns the message.
        message_id: Identifier of the message to edit.
        text: New message body.
        reply_markup: Optional updated inline keyboard dict.
        client: Optional injected ``httpx.AsyncClient`` (for tests).
    """
    payload: dict = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    await _post(_EDIT_MESSAGE_URL.format(token=token), payload, client=client)


async def answer_callback_query(
    token: str,
    callback_query_id: str,
    *,
    text: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> None:
    """Answer a callback query to dismiss the loading indicator in Telegram.

    Args:
        token: Telegram bot token.
        callback_query_id: Identifier from the incoming ``CallbackQuery``.
        text: Optional short notification text shown to the user (toast).
        client: Optional injected ``httpx.AsyncClient`` (for tests).
    """
    payload: dict = {"callback_query_id": callback_query_id}
    if text is not None:
        payload["text"] = text
    await _post(_ANSWER_CALLBACK_URL.format(token=token), payload, client=client)
