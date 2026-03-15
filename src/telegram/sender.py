"""Outgoing Telegram message helpers.

Sends replies via the Telegram Bot API using httpx.  An optional pre-built
``httpx.AsyncClient`` can be injected for testing without real network calls.
"""

import httpx

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


async def send_message(
    token: str,
    chat_id: int,
    text: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> None:
    """POST a text message to *chat_id* via the Telegram Bot API.

    Args:
        token: Telegram bot token from ``Settings.telegram_bot_token``.
        chat_id: Target chat identifier.
        text: Message body (HTML parse mode enabled).
        client: Optional injected ``httpx.AsyncClient`` (for tests).
    """
    url = _TELEGRAM_API.format(token=token)
    payload = {"chat_id": chat_id, "text": text}

    if client is not None:
        await client.post(url, json=payload)
    else:
        async with httpx.AsyncClient() as c:
            await c.post(url, json=payload)
