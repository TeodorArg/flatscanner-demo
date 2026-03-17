"""Minimal OpenRouter HTTP client.

Wraps the OpenRouter chat completions endpoint (OpenAI-compatible API).
Authentication uses an ``Authorization: Bearer <key>`` header.

Usage
-----
    client = OpenRouterClient(api_key="sk-or-...", model="anthropic/claude-3-haiku")
    text = await client.chat([{"role": "user", "content": "Hello"}])
"""

from __future__ import annotations

from typing import Any

import httpx

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Generous default timeout: the model may need several seconds to respond.
DEFAULT_TIMEOUT = 60.0


class OpenRouterError(Exception):
    """Raised when the OpenRouter API returns an error or an unexpected response."""


class OpenRouterClient:
    """Thin async wrapper around the OpenRouter chat completions API.

    Parameters
    ----------
    api_key:
        OpenRouter API key (``OPENROUTER_API_KEY`` env variable).
    model:
        Model identifier as accepted by OpenRouter, e.g.
        ``"anthropic/claude-3-haiku"``.
    timeout:
        HTTP request timeout in seconds (default 60).
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    async def chat(self, messages: list[dict[str, Any]]) -> str:
        """Send *messages* to the chat completions endpoint and return the reply.

        Parameters
        ----------
        messages:
            List of message dicts with ``role`` and ``content`` keys, following
            the OpenAI chat format.

        Returns
        -------
        str
            The text content of the first choice's message.

        Raises
        ------
        OpenRouterError
            If the API returns a non-200 status, a missing ``choices`` field,
            any other unexpected response shape, or the request times out.
        """
        url = f"{OPENROUTER_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
            except httpx.TimeoutException as exc:
                raise OpenRouterError(
                    f"OpenRouter request timed out after {self._timeout}s"
                ) from exc

        if response.status_code != 200:
            raise OpenRouterError(
                f"OpenRouter request failed with status {response.status_code}: "
                f"{response.text[:400]}"
            )

        body: Any = response.json()
        if not isinstance(body, dict):
            raise OpenRouterError(
                f"Unexpected OpenRouter response type: expected dict, "
                f"got {type(body).__name__}"
            )

        choices = body.get("choices")
        if not isinstance(choices, list) or len(choices) == 0:
            raise OpenRouterError(
                "OpenRouter response missing 'choices' or choices list is empty"
            )

        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str):
            raise OpenRouterError(
                f"OpenRouter choice message 'content' is not a string: {content!r}"
            )

        return content
