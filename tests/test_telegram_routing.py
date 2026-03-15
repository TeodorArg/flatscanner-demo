"""Tests for Telegram bot entrypoints and message routing."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app.config import Settings
from src.app.main import create_app
from src.telegram.dispatcher import extract_url, route_update
from src.telegram.models import TelegramChat, TelegramMessage, TelegramUpdate, TelegramUser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_update(
    text: str | None,
    chat_id: int = 1001,
    update_id: int = 1,
) -> TelegramUpdate:
    user = TelegramUser(id=42, first_name="Alice")
    chat = TelegramChat(id=chat_id, type="private")
    message = TelegramMessage(
        message_id=1,
        **{"from": user},
        chat=chat,
        text=text,
    )
    return TelegramUpdate(update_id=update_id, message=message)


def _test_settings(**overrides) -> Settings:
    defaults = {
        "app_env": "testing",
        "telegram_bot_token": "test-token",
        "openrouter_api_key": "test-key",
        "apify_api_token": "test-apify",
        "database_url": "postgresql://test:test@localhost:5432/test",
        "redis_url": "redis://localhost:6379/1",
    }
    defaults.update(overrides)
    return Settings(**defaults)


# ---------------------------------------------------------------------------
# extract_url
# ---------------------------------------------------------------------------


class TestExtractUrl:
    def test_returns_url_from_plain_text(self):
        assert extract_url("Check this out: https://www.airbnb.com/rooms/123") == (
            "https://www.airbnb.com/rooms/123"
        )

    def test_returns_none_when_no_url(self):
        assert extract_url("Hello, how are you?") is None

    def test_strips_trailing_punctuation(self):
        result = extract_url("See https://example.com/listing.")
        assert result == "https://example.com/listing"

    def test_http_url(self):
        assert extract_url("http://example.com/flat") == "http://example.com/flat"

    def test_returns_first_url_when_multiple(self):
        text = "https://airbnb.com/1 and https://booking.com/2"
        assert extract_url(text) == "https://airbnb.com/1"

    def test_empty_string_returns_none(self):
        assert extract_url("") is None


# ---------------------------------------------------------------------------
# route_update
# ---------------------------------------------------------------------------


class TestRouteUpdate:
    def test_analyse_when_url_present(self):
        update = _make_update("https://www.airbnb.com/rooms/999", chat_id=5)
        decision = route_update(update)
        assert decision["action"] == "analyse"
        assert decision["url"] == "https://www.airbnb.com/rooms/999"
        assert decision["chat_id"] == 5

    def test_help_when_no_url(self):
        update = _make_update("What can you do?", chat_id=7)
        decision = route_update(update)
        assert decision["action"] == "help"
        assert decision["chat_id"] == 7

    def test_ignore_when_no_message(self):
        update = TelegramUpdate(update_id=1, message=None)
        decision = route_update(update)
        assert decision["action"] == "ignore"

    def test_ignore_when_no_text(self):
        update = _make_update(text=None)
        decision = route_update(update)
        assert decision["action"] == "ignore"

    def test_ignore_when_empty_text(self):
        # Empty string is falsy — treated as no text
        update = _make_update(text="")
        decision = route_update(update)
        assert decision["action"] == "ignore"


# ---------------------------------------------------------------------------
# TelegramUpdate model parsing
# ---------------------------------------------------------------------------


class TestTelegramModels:
    def test_parse_update_with_from_field(self):
        raw = {
            "update_id": 100,
            "message": {
                "message_id": 1,
                "from": {"id": 42, "first_name": "Alice"},
                "chat": {"id": 1001, "type": "private"},
                "text": "hello",
            },
        }
        update = TelegramUpdate.model_validate(raw)
        assert update.message is not None
        assert update.message.from_ is not None
        assert update.message.from_.first_name == "Alice"
        assert update.message.text == "hello"

    def test_parse_update_without_message(self):
        raw = {"update_id": 200}
        update = TelegramUpdate.model_validate(raw)
        assert update.message is None


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------


class TestWebhookEndpoint:
    def _client(self, **settings_overrides) -> TestClient:
        return TestClient(create_app(settings=_test_settings(**settings_overrides)))

    def _update_payload(self, text: str | None, chat_id: int = 1001) -> dict:
        payload: dict = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "from": {"id": 42, "first_name": "Alice"},
                "chat": {"id": chat_id, "type": "private"},
            },
        }
        if text is not None:
            payload["message"]["text"] = text
        return payload

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_webhook_url_triggers_analyse_reply(self, mock_send):
        client = self._client()
        payload = self._update_payload("https://www.airbnb.com/rooms/123", chat_id=1001)
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        mock_send.assert_awaited_once()
        _, call_kwargs = mock_send.call_args
        # Positional: (token, chat_id, text)
        call_args = mock_send.call_args[0]
        assert call_args[1] == 1001
        assert "airbnb.com/rooms/123" in call_args[2]

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_webhook_plain_text_triggers_help_reply(self, mock_send):
        client = self._client()
        payload = self._update_payload("What listing platforms do you support?")
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        mock_send.assert_awaited_once()
        call_args = mock_send.call_args[0]
        assert "URL" in call_args[2] or "url" in call_args[2].lower()

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_webhook_no_text_returns_ok_without_send(self, mock_send):
        client = self._client()
        payload = self._update_payload(text=None)
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        mock_send.assert_not_awaited()

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_webhook_uses_bot_token_from_settings(self, mock_send):
        client = self._client(telegram_bot_token="my-secret-token")
        payload = self._update_payload("https://airbnb.com/rooms/1")
        client.post("/telegram/webhook", json=payload)
        call_args = mock_send.call_args[0]
        assert call_args[0] == "my-secret-token"

    def test_webhook_rejects_invalid_payload(self):
        client = self._client()
        response = client.post("/telegram/webhook", json={"bad": "data"})
        assert response.status_code == 422
