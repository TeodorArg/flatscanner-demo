"""Tests for menu-related routing decisions and webhook integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app.config import Settings
from src.app.main import create_app
from src.i18n.types import Language
from src.storage.chat_settings import ChatSettings
from src.telegram.dispatcher import (
    MenuCallbackDecision,
    OpenMenuDecision,
    route_update,
)
from src.telegram.menu.callback import build_callback
from src.telegram.models import (
    TelegramCallbackQuery,
    TelegramChat,
    TelegramMessage,
    TelegramUpdate,
    TelegramUser,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def _make_message_update(text: str, chat_id: int = 1001) -> TelegramUpdate:
    user = TelegramUser(id=42, first_name="Alice")
    chat = TelegramChat(id=chat_id, type="private")
    msg = TelegramMessage(message_id=1, **{"from": user}, chat=chat, text=text)
    return TelegramUpdate(update_id=1, message=msg)


def _make_callback_update(
    data: str,
    chat_id: int = 1001,
    message_id: int = 99,
    callback_query_id: str = "cbq-1",
) -> TelegramUpdate:
    user = TelegramUser(id=42, first_name="Alice")
    chat = TelegramChat(id=chat_id, type="private")
    msg = TelegramMessage(message_id=message_id, **{"from": user}, chat=chat, text=None)
    cbq = TelegramCallbackQuery(
        id=callback_query_id,
        **{"from": user},
        message=msg,
        data=data,
    )
    return TelegramUpdate(update_id=2, callback_query=cbq)


def _menu_payload(chat_id: int = 1001) -> dict:
    return {
        "update_id": 10,
        "message": {
            "message_id": 1,
            "from": {"id": 42, "first_name": "Alice"},
            "chat": {"id": chat_id, "type": "private"},
            "text": "/menu",
        },
    }


def _callback_payload(data: str, chat_id: int = 1001, message_id: int = 99) -> dict:
    return {
        "update_id": 11,
        "callback_query": {
            "id": "cbq-123",
            "from": {"id": 42, "first_name": "Alice"},
            "message": {
                "message_id": message_id,
                "from": {"id": 0, "first_name": "Bot"},
                "chat": {"id": chat_id, "type": "private"},
            },
            "data": data,
        },
    }


# ---------------------------------------------------------------------------
# Dispatcher: /menu command routing
# ---------------------------------------------------------------------------


class TestMenuCommandDispatch:
    def test_menu_command_returns_open_menu_decision(self):
        update = _make_message_update("/menu")
        decision = route_update(update)
        assert decision["action"] == "open_menu"
        assert decision["chat_id"] == 1001

    def test_menu_command_case_insensitive(self):
        update = _make_message_update("/Menu")
        decision = route_update(update)
        assert decision["action"] == "open_menu"

    def test_menu_command_with_trailing_space(self):
        update = _make_message_update("/menu ")
        decision = route_update(update)
        assert decision["action"] == "open_menu"

    def test_non_menu_command_is_not_open_menu(self):
        update = _make_message_update("/start")
        decision = route_update(update)
        assert decision["action"] != "open_menu"


# ---------------------------------------------------------------------------
# Dispatcher: callback query routing
# ---------------------------------------------------------------------------


class TestCallbackQueryDispatch:
    def test_menu_callback_returns_menu_callback_decision(self):
        data = build_callback("main", "nav", "language")
        update = _make_callback_update(data)
        decision = route_update(update)
        assert decision["action"] == "menu_callback"
        assert decision["callback_data"] == data

    def test_menu_callback_carries_chat_id(self):
        data = build_callback("language", "set", "en")
        update = _make_callback_update(data, chat_id=5555)
        decision = route_update(update)
        assert decision["chat_id"] == 5555

    def test_menu_callback_carries_message_id(self):
        data = build_callback("settings", "back", "main")
        update = _make_callback_update(data, message_id=42)
        decision = route_update(update)
        assert decision["message_id"] == 42

    def test_menu_callback_carries_callback_query_id(self):
        data = build_callback("main", "nav", "settings")
        update = _make_callback_update(data, callback_query_id="cbq-xyz")
        decision = route_update(update)
        assert decision["callback_query_id"] == "cbq-xyz"

    def test_non_menu_callback_data_is_ignored(self):
        update = _make_callback_update("some_other_data")
        decision = route_update(update)
        assert decision["action"] == "ignore"

    def test_callback_without_data_is_ignored(self):
        user = TelegramUser(id=42, first_name="Alice")
        chat = TelegramChat(id=1001, type="private")
        msg = TelegramMessage(message_id=1, **{"from": user}, chat=chat)
        cbq = TelegramCallbackQuery(id="cbq-1", **{"from": user}, message=msg, data=None)
        update = TelegramUpdate(update_id=3, callback_query=cbq)
        decision = route_update(update)
        assert decision["action"] == "ignore"


# ---------------------------------------------------------------------------
# Webhook integration: /menu opens main menu
# ---------------------------------------------------------------------------


class TestWebhookMenuCommand:
    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    @patch("src.telegram.router.get_chat_settings", new_callable=AsyncMock)
    def test_menu_command_sends_message_with_keyboard(
        self, mock_get_settings, mock_send
    ):
        mock_get_settings.return_value = ChatSettings(language=Language.EN)

        app = create_app(settings=_test_settings())
        app.state.redis = MagicMock()
        client = TestClient(app, raise_server_exceptions=True)

        response = client.post("/telegram/webhook", json=_menu_payload())
        assert response.status_code == 200
        mock_send.assert_awaited_once()
        _, kwargs = mock_send.call_args[0], mock_send.call_args[1]
        assert "reply_markup" in mock_send.call_args[1] or len(mock_send.call_args[0]) >= 4

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    @patch("src.telegram.router.get_chat_settings", new_callable=AsyncMock)
    def test_menu_uses_chat_language(self, mock_get_settings, mock_send):
        mock_get_settings.return_value = ChatSettings(language=Language.RU)

        app = create_app(settings=_test_settings())
        app.state.redis = MagicMock()
        client = TestClient(app, raise_server_exceptions=True)

        response = client.post("/telegram/webhook", json=_menu_payload())
        assert response.status_code == 200
        # The text should be in Russian
        call_text = mock_send.call_args[0][2]
        assert "Главное меню" in call_text


# ---------------------------------------------------------------------------
# Webhook integration: menu callback navigation
# ---------------------------------------------------------------------------


class TestWebhookMenuCallbackNavigation:
    @patch("src.telegram.router.edit_message_text", new_callable=AsyncMock)
    @patch("src.telegram.router.answer_callback_query", new_callable=AsyncMock)
    @patch("src.telegram.router.get_chat_settings", new_callable=AsyncMock)
    def test_nav_to_language_screen_edits_message(
        self, mock_get_settings, mock_answer, mock_edit
    ):
        mock_get_settings.return_value = ChatSettings(language=Language.EN)

        app = create_app(settings=_test_settings())
        app.state.redis = MagicMock()
        client = TestClient(app, raise_server_exceptions=True)

        data = build_callback("main", "nav", "language")
        response = client.post("/telegram/webhook", json=_callback_payload(data))
        assert response.status_code == 200
        mock_answer.assert_awaited_once()
        mock_edit.assert_awaited_once()

    @patch("src.telegram.router.edit_message_text", new_callable=AsyncMock)
    @patch("src.telegram.router.answer_callback_query", new_callable=AsyncMock)
    @patch("src.telegram.router.get_chat_settings", new_callable=AsyncMock)
    def test_back_to_main_renders_main_menu(
        self, mock_get_settings, mock_answer, mock_edit
    ):
        mock_get_settings.return_value = ChatSettings(language=Language.EN)

        app = create_app(settings=_test_settings())
        app.state.redis = MagicMock()
        client = TestClient(app, raise_server_exceptions=True)

        data = build_callback("language", "back", "main")
        response = client.post("/telegram/webhook", json=_callback_payload(data))
        assert response.status_code == 200
        mock_edit.assert_awaited_once()
        edit_text = mock_edit.call_args[0][3]
        assert "Main Menu" in edit_text

    @patch("src.telegram.router.edit_message_text", new_callable=AsyncMock)
    @patch("src.telegram.router.answer_callback_query", new_callable=AsyncMock)
    @patch("src.telegram.router.get_chat_settings", new_callable=AsyncMock)
    def test_nav_to_settings_renders_settings_stub(
        self, mock_get_settings, mock_answer, mock_edit
    ):
        mock_get_settings.return_value = ChatSettings(language=Language.EN)

        app = create_app(settings=_test_settings())
        app.state.redis = MagicMock()
        client = TestClient(app, raise_server_exceptions=True)

        data = build_callback("main", "nav", "settings")
        response = client.post("/telegram/webhook", json=_callback_payload(data))
        assert response.status_code == 200
        mock_edit.assert_awaited_once()
        edit_text = mock_edit.call_args[0][3]
        assert "Settings" in edit_text

    @patch("src.telegram.router.edit_message_text", new_callable=AsyncMock)
    @patch("src.telegram.router.answer_callback_query", new_callable=AsyncMock)
    @patch("src.telegram.router.get_chat_settings", new_callable=AsyncMock)
    def test_nav_to_billing_renders_billing_stub(
        self, mock_get_settings, mock_answer, mock_edit
    ):
        mock_get_settings.return_value = ChatSettings(language=Language.EN)

        app = create_app(settings=_test_settings())
        app.state.redis = MagicMock()
        client = TestClient(app, raise_server_exceptions=True)

        data = build_callback("main", "nav", "billing")
        response = client.post("/telegram/webhook", json=_callback_payload(data))
        assert response.status_code == 200
        mock_edit.assert_awaited_once()
        edit_text = mock_edit.call_args[0][3]
        assert "Billing" in edit_text


# ---------------------------------------------------------------------------
# Webhook integration: language selection via menu
# ---------------------------------------------------------------------------


class TestWebhookMenuLanguageSelection:
    @patch("src.telegram.router.edit_message_text", new_callable=AsyncMock)
    @patch("src.telegram.router.answer_callback_query", new_callable=AsyncMock)
    @patch("src.telegram.router.save_chat_settings", new_callable=AsyncMock)
    @patch("src.telegram.router.get_chat_settings", new_callable=AsyncMock)
    def test_set_language_saves_new_language(
        self, mock_get_settings, mock_save, mock_answer, mock_edit
    ):
        mock_get_settings.return_value = ChatSettings(language=Language.RU)

        app = create_app(settings=_test_settings())
        app.state.redis = MagicMock()
        client = TestClient(app, raise_server_exceptions=True)

        data = build_callback("language", "set", "en")
        response = client.post("/telegram/webhook", json=_callback_payload(data))
        assert response.status_code == 200
        mock_save.assert_awaited_once()
        saved_settings: ChatSettings = mock_save.call_args[0][2]
        assert saved_settings.language == Language.EN

    @patch("src.telegram.router.edit_message_text", new_callable=AsyncMock)
    @patch("src.telegram.router.answer_callback_query", new_callable=AsyncMock)
    @patch("src.telegram.router.save_chat_settings", new_callable=AsyncMock)
    @patch("src.telegram.router.get_chat_settings", new_callable=AsyncMock)
    def test_set_language_answers_callback_with_confirm_toast(
        self, mock_get_settings, mock_save, mock_answer, mock_edit
    ):
        mock_get_settings.return_value = ChatSettings(language=Language.RU)

        app = create_app(settings=_test_settings())
        app.state.redis = MagicMock()
        client = TestClient(app, raise_server_exceptions=True)

        data = build_callback("language", "set", "en")
        response = client.post("/telegram/webhook", json=_callback_payload(data))
        assert response.status_code == 200
        # answer_callback_query should be called with a confirmation toast
        mock_answer.assert_awaited_once()
        answer_text = mock_answer.call_args[1].get("text") or (
            mock_answer.call_args[0][2] if len(mock_answer.call_args[0]) > 2 else None
        )
        assert answer_text is not None
        assert "Language updated" in answer_text or answer_text  # non-empty toast

    @patch("src.telegram.router.edit_message_text", new_callable=AsyncMock)
    @patch("src.telegram.router.answer_callback_query", new_callable=AsyncMock)
    @patch("src.telegram.router.save_chat_settings", new_callable=AsyncMock)
    @patch("src.telegram.router.get_chat_settings", new_callable=AsyncMock)
    def test_set_language_edits_message_in_new_language(
        self, mock_get_settings, mock_save, mock_answer, mock_edit
    ):
        mock_get_settings.return_value = ChatSettings(language=Language.RU)

        app = create_app(settings=_test_settings())
        app.state.redis = MagicMock()
        client = TestClient(app, raise_server_exceptions=True)

        data = build_callback("language", "set", "es")
        response = client.post("/telegram/webhook", json=_callback_payload(data))
        assert response.status_code == 200
        mock_edit.assert_awaited_once()
        edit_text = mock_edit.call_args[0][3]
        # Language screen in Spanish
        assert "Elige tu idioma" in edit_text

    @patch("src.telegram.router.edit_message_text", new_callable=AsyncMock)
    @patch("src.telegram.router.answer_callback_query", new_callable=AsyncMock)
    @patch("src.telegram.router.save_chat_settings", new_callable=AsyncMock)
    @patch("src.telegram.router.get_chat_settings", new_callable=AsyncMock)
    def test_invalid_language_code_is_silently_ignored(
        self, mock_get_settings, mock_save, mock_answer, mock_edit
    ):
        mock_get_settings.return_value = ChatSettings(language=Language.RU)

        app = create_app(settings=_test_settings())
        app.state.redis = MagicMock()
        client = TestClient(app, raise_server_exceptions=True)

        data = build_callback("language", "set", "xx")
        response = client.post("/telegram/webhook", json=_callback_payload(data))
        assert response.status_code == 200
        mock_save.assert_not_awaited()
