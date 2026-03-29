"""Outgoing Telegram message helpers.

Sends replies via the Telegram Bot API using httpx.  An optional pre-built
``httpx.AsyncClient`` can be injected for testing without real network calls.
"""

import httpx

_BASE = "https://api.telegram.org/bot{token}"
_SEND_MESSAGE_URL = _BASE + "/sendMessage"
_EDIT_MESSAGE_URL = _BASE + "/editMessageText"
_ANSWER_CALLBACK_URL = _BASE + "/answerCallbackQuery"
_SEND_CHAT_ACTION_URL = _BASE + "/sendChatAction"
_DELETE_MESSAGE_URL = _BASE + "/deleteMessage"


async def _post(url: str, payload: dict, *, client: httpx.AsyncClient | None) -> None:
    if client is not None:
        response = await client.post(url, json=payload)
        response.raise_for_status()
    else:
        async with httpx.AsyncClient() as c:
            response = await c.post(url, json=payload)
            response.raise_for_status()


async def _post_json(url: str, payload: dict, *, client: httpx.AsyncClient | None) -> dict:
    if client is not None:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    else:
        async with httpx.AsyncClient() as c:
            response = await c.post(url, json=payload)
            response.raise_for_status()
            return response.json()


async def send_message(
    token: str,
    chat_id: int,
    text: str,
    *,
    reply_markup: dict | None = None,
    parse_mode: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> None:
    """POST a text message to *chat_id* via the Telegram Bot API.

    Args:
        token: Telegram bot token from ``Settings.telegram_bot_token``.
        chat_id: Target chat identifier.
        text: Message body (plain text).
        reply_markup: Optional inline keyboard or other reply markup dict.
        parse_mode: Optional Telegram parse mode (e.g. ``"HTML"``).
        client: Optional injected ``httpx.AsyncClient`` (for tests).
    """
    payload: dict = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    if parse_mode is not None:
        payload["parse_mode"] = parse_mode
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


async def send_message_return_id(
    token: str,
    chat_id: int,
    text: str,
    *,
    parse_mode: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> int:
    """POST a text message and return the Telegram message_id of the sent message.

    Args:
        token: Telegram bot token.
        chat_id: Target chat identifier.
        text: Message body.
        parse_mode: Optional Telegram parse mode (e.g. ``"HTML"``).
        client: Optional injected ``httpx.AsyncClient`` (for tests).

    Returns:
        The ``message_id`` assigned by Telegram to the sent message.
    """
    payload: dict = {"chat_id": chat_id, "text": text}
    if parse_mode is not None:
        payload["parse_mode"] = parse_mode
    data = await _post_json(_SEND_MESSAGE_URL.format(token=token), payload, client=client)
    return data["result"]["message_id"]


async def send_chat_action(
    token: str,
    chat_id: int,
    action: str = "typing",
    *,
    client: httpx.AsyncClient | None = None,
) -> None:
    """Send a chat action (e.g. typing indicator) via the Telegram Bot API.

    Args:
        token: Telegram bot token.
        chat_id: Target chat identifier.
        action: Action string (default ``"typing"``).
        client: Optional injected ``httpx.AsyncClient`` (for tests).
    """
    payload: dict = {"chat_id": chat_id, "action": action}
    await _post(_SEND_CHAT_ACTION_URL.format(token=token), payload, client=client)


async def delete_message(
    token: str,
    chat_id: int,
    message_id: int,
    *,
    client: httpx.AsyncClient | None = None,
) -> None:
    """Delete a message via the Telegram Bot API.

    Args:
        token: Telegram bot token.
        chat_id: Chat that owns the message.
        message_id: Identifier of the message to delete.
        client: Optional injected ``httpx.AsyncClient`` (for tests).
    """
    payload: dict = {"chat_id": chat_id, "message_id": message_id}
    await _post(_DELETE_MESSAGE_URL.format(token=token), payload, client=client)
