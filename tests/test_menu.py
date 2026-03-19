"""Tests for the Telegram inline-menu foundation.

Covers:
- Callback payload parsing and building (menu.callback)
- Menu screen rendering in all supported languages (menu.screens)
- /menu command routing (dispatcher)
- Callback-query routing (dispatcher)
- ChatSettings persistence (storage.chat_settings)
- /menu and menu-based language selection via the webhook (router)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from src.app.config import Settings
from src.app.main import create_app
from src.i18n.types import DEFAULT_LANGUAGE, Language
from src.storage.chat_settings import ChatSettings, get_chat_settings, save_chat_settings
from src.telegram.dispatcher import route_update
from src.telegram.menu.callback import (
    MenuCallback,
    build_callback,
    is_menu_callback,
    parse_callback,
)
from src.telegram.menu.screens import (
    SCREEN_RENDERERS,
    render_billing_screen,
    render_help_screen,
    render_language_screen,
    render_main_menu,
    render_settings_screen,
)
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


def _make_message_update(
    text: str,
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


def _make_callback_update(
    data: str,
    chat_id: int = 1001,
    message_id: int = 100,
    update_id: int = 2,
) -> TelegramUpdate:
    user = TelegramUser(id=42, first_name="Alice")
    chat = TelegramChat(id=chat_id, type="private")
    message = TelegramMessage(
        message_id=message_id,
        **{"from": user},
        chat=chat,
        text=None,
    )
    callback_query = TelegramCallbackQuery(
        id="cbq-001",
        **{"from": user},
        message=message,
        data=data,
    )
    return TelegramUpdate(update_id=update_id, callback_query=callback_query)


# ---------------------------------------------------------------------------
# Callback payload parsing
# ---------------------------------------------------------------------------


class TestBuildCallback:
    def test_produces_correct_format(self):
        result = build_callback("main", "nav", "language")
        assert result == "menu:main:nav:language"

    def test_language_set_payload(self):
        assert build_callback("language", "set", "ru") == "menu:language:set:ru"

    def test_back_payload(self):
        assert build_callback("language", "back", "main") == "menu:language:back:main"


class TestParseCallback:
    def test_valid_nav_payload(self):
        cb = parse_callback("menu:main:nav:language")
        assert cb is not None
        assert cb.screen == "main"
        assert cb.action == "nav"
        assert cb.value == "language"

    def test_valid_set_payload(self):
        cb = parse_callback("menu:language:set:en")
        assert cb is not None
        assert cb.screen == "language"
        assert cb.action == "set"
        assert cb.value == "en"

    def test_valid_back_payload(self):
        cb = parse_callback("menu:language:back:main")
        assert cb is not None
        assert cb.screen == "language"
        assert cb.action == "back"
        assert cb.value == "main"

    def test_returns_none_for_wrong_prefix(self):
        assert parse_callback("other:language:set:en") is None

    def test_returns_none_for_missing_parts(self):
        assert parse_callback("menu:language:set") is None

    def test_returns_none_for_empty_string(self):
        assert parse_callback("") is None

    def test_returns_none_for_prefix_only(self):
        assert parse_callback("menu") is None

    def test_returns_none_when_screen_is_empty(self):
        assert parse_callback("menu::set:en") is None

    def test_returns_none_when_action_is_empty(self):
        assert parse_callback("menu:language::en") is None

    def test_returns_none_when_value_is_empty(self):
        assert parse_callback("menu:language:set:") is None

    def test_roundtrip_via_build_and_parse(self):
        original = build_callback("billing", "back", "main")
        parsed = parse_callback(original)
        assert parsed == MenuCallback(screen="billing", action="back", value="main")


class TestIsMenuCallback:
    def test_returns_true_for_menu_prefix(self):
        assert is_menu_callback("menu:main:nav:language") is True

    def test_returns_false_for_non_menu_prefix(self):
        assert is_menu_callback("other:something") is False

    def test_returns_false_for_empty_string(self):
        assert is_menu_callback("") is False

    def test_returns_false_for_plain_menu(self):
        assert is_menu_callback("menu") is False


# ---------------------------------------------------------------------------
# Screen rendering
# ---------------------------------------------------------------------------


class TestRenderMainMenu:
    def test_returns_text_and_markup(self):
        text, markup = render_main_menu(Language.EN)
        assert isinstance(text, str)
        assert len(text) > 0
        assert "inline_keyboard" in markup

    def test_has_four_buttons(self):
        _, markup = render_main_menu(Language.EN)
        buttons = [btn for row in markup["inline_keyboard"] for btn in row]
        assert len(buttons) == 4

    def test_buttons_have_menu_callbacks(self):
        _, markup = render_main_menu(Language.EN)
        for row in markup["inline_keyboard"]:
            for btn in row:
                assert btn["callback_data"].startswith("menu:")

    def test_language_button_navigates_to_language_screen(self):
        _, markup = render_main_menu(Language.EN)
        all_callbacks = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert build_callback("main", "nav", "language") in all_callbacks

    def test_settings_button_navigates_to_settings_screen(self):
        _, markup = render_main_menu(Language.EN)
        all_callbacks = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert build_callback("main", "nav", "settings") in all_callbacks

    def test_billing_button_navigates_to_billing_screen(self):
        _, markup = render_main_menu(Language.EN)
        all_callbacks = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert build_callback("main", "nav", "billing") in all_callbacks

    def test_help_button_navigates_to_help_screen(self):
        _, markup = render_main_menu(Language.EN)
        all_callbacks = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert build_callback("main", "nav", "help") in all_callbacks

    def test_russian_locale(self):
        text, markup = render_main_menu(Language.RU)
        assert isinstance(text, str)
        # Buttons should exist
        buttons = [btn for row in markup["inline_keyboard"] for btn in row]
        assert len(buttons) == 4

    def test_spanish_locale(self):
        text, markup = render_main_menu(Language.ES)
        buttons = [btn for row in markup["inline_keyboard"] for btn in row]
        assert len(buttons) == 4


class TestRenderLanguageScreen:
    def test_has_three_language_buttons_plus_back(self):
        _, markup = render_language_screen(Language.EN)
        buttons = [btn for row in markup["inline_keyboard"] for btn in row]
        assert len(buttons) == 4  # ru, en, es + back

    def test_ru_button_sets_russian(self):
        _, markup = render_language_screen(Language.EN)
        all_callbacks = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert build_callback("language", "set", "ru") in all_callbacks

    def test_en_button_sets_english(self):
        _, markup = render_language_screen(Language.EN)
        all_callbacks = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert build_callback("language", "set", "en") in all_callbacks

    def test_es_button_sets_spanish(self):
        _, markup = render_language_screen(Language.EN)
        all_callbacks = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert build_callback("language", "set", "es") in all_callbacks

    def test_back_button_returns_to_main(self):
        _, markup = render_language_screen(Language.EN)
        all_callbacks = [btn["callback_data"] for row in markup["inline_keyboard"] for btn in row]
        assert build_callback("language", "back", "main") in all_callbacks


class TestRenderSettingsScreen:
    def test_has_back_button(self):
        _, markup = render_settings_screen(Language.EN)
        buttons = [btn for row in markup["inline_keyboard"] for btn in row]
        callbacks = [btn["callback_data"] for btn in buttons]
        assert build_callback("settings", "back", "main") in callbacks

    def test_text_is_non_empty(self):
        text, _ = render_settings_screen(Language.EN)
        assert len(text) > 0


class TestRenderBillingScreen:
    def test_has_back_button(self):
        _, markup = render_billing_screen(Language.EN)
        buttons = [btn for row in markup["inline_keyboard"] for btn in row]
        callbacks = [btn["callback_data"] for btn in buttons]
        assert build_callback("billing", "back", "main") in callbacks

    def test_text_is_non_empty(self):
        text, _ = render_billing_screen(Language.EN)
        assert len(text) > 0


class TestRenderHelpScreen:
    def test_has_back_button(self):
        _, markup = render_help_screen(Language.EN)
        buttons = [btn for row in markup["inline_keyboard"] for btn in row]
        callbacks = [btn["callback_data"] for btn in buttons]
        assert build_callback("help", "back", "main") in callbacks

    def test_text_is_non_empty(self):
        text, _ = render_help_screen(Language.EN)
        assert len(text) > 0


class TestScreenRenderers:
    def test_all_screens_are_registered(self):
        expected = {"main", "language", "settings", "billing", "help"}
        assert set(SCREEN_RENDERERS.keys()) == expected

    def test_each_renderer_returns_tuple(self):
        for name, renderer in SCREEN_RENDERERS.items():
            result = renderer(Language.EN)
            assert isinstance(result, tuple), f"{name} renderer did not return a tuple"
            assert len(result) == 2, f"{name} renderer did not return a 2-tuple"


# ---------------------------------------------------------------------------
# Dispatcher: /menu command routing
# ---------------------------------------------------------------------------


class TestMenuCommandRouting:
    def test_menu_command_routes_to_open_menu(self):
        update = _make_message_update("/menu", chat_id=42)
        decision = route_update(update)
        assert decision["action"] == "open_menu"
        assert decision["chat_id"] == 42

    def test_menu_command_case_insensitive(self):
        update = _make_message_update("/MENU", chat_id=42)
        decision = route_update(update)
        assert decision["action"] == "open_menu"

    def test_menu_command_with_trailing_whitespace(self):
        update = _make_message_update("/menu  ", chat_id=42)
        decision = route_update(update)
        assert decision["action"] == "open_menu"

    def test_menu_command_does_not_match_url(self):
        update = _make_message_update("https://www.airbnb.com/rooms/123 /menu", chat_id=42)
        decision = route_update(update)
        # URL is present — should route to analyse, not open_menu
        assert decision["action"] == "analyse"

    def test_non_menu_text_routes_to_help(self):
        update = _make_message_update("hello bot", chat_id=42)
        decision = route_update(update)
        assert decision["action"] == "help"


# ---------------------------------------------------------------------------
# Dispatcher: callback query routing
# ---------------------------------------------------------------------------


class TestCallbackQueryRouting:
    def test_menu_callback_routes_to_menu_callback(self):
        update = _make_callback_update("menu:main:nav:language", chat_id=1001, message_id=50)
        decision = route_update(update)
        assert decision["action"] == "menu_callback"

    def test_menu_callback_includes_correct_fields(self):
        update = _make_callback_update(
            "menu:language:set:ru", chat_id=1001, message_id=77
        )
        decision = route_update(update)
        assert decision["action"] == "menu_callback"
        assert decision["chat_id"] == 1001
        assert decision["message_id"] == 77
        assert decision["callback_query_id"] == "cbq-001"
        assert decision["callback_data"] == "menu:language:set:ru"

    def test_non_menu_callback_routes_to_ignore(self):
        user = TelegramUser(id=42, first_name="Alice")
        chat = TelegramChat(id=1001, type="private")
        message = TelegramMessage(
            message_id=1,
            **{"from": user},
            chat=chat,
            text=None,
        )
        cq = TelegramCallbackQuery(
            id="cbq-002",
            **{"from": user},
            message=message,
            data="other:whatever",
        )
        update = TelegramUpdate(update_id=3, callback_query=cq)
        decision = route_update(update)
        assert decision["action"] == "ignore"

    def test_callback_without_message_routes_to_ignore(self):
        """Callback query with no attached message is not routable (no message_id)."""
        user = TelegramUser(id=42, first_name="Alice")
        cq = TelegramCallbackQuery(
            id="cbq-003",
            **{"from": user},
            message=None,
            data="menu:main:nav:language",
        )
        update = TelegramUpdate(update_id=4, callback_query=cq)
        decision = route_update(update)
        # No message → ignore (can't edit a non-existent message)
        assert decision["action"] == "ignore"


# ---------------------------------------------------------------------------
# ChatSettings persistence
# ---------------------------------------------------------------------------


class TestChatSettings:
    def test_default_language_is_ru(self):
        settings = ChatSettings()
        assert settings.language == DEFAULT_LANGUAGE
        assert settings.language == Language.RU

    def test_can_set_language(self):
        settings = ChatSettings(language=Language.EN)
        assert settings.language == Language.EN

    @pytest.mark.asyncio
    async def test_get_chat_settings_returns_default_when_no_key(self):
        redis = AsyncMock()
        redis.get.return_value = None
        result = await get_chat_settings(redis, chat_id=1001)
        assert result.language == DEFAULT_LANGUAGE

    @pytest.mark.asyncio
    async def test_get_chat_settings_returns_stored_language(self):
        redis = AsyncMock()
        redis.get.return_value = b"en"
        result = await get_chat_settings(redis, chat_id=1001)
        assert result.language == Language.EN

    @pytest.mark.asyncio
    async def test_save_chat_settings_persists_language(self):
        redis = AsyncMock()
        settings = ChatSettings(language=Language.ES)
        await save_chat_settings(redis, chat_id=42, settings=settings)
        redis.set.assert_awaited_once()
        # The key and value args
        call_args = redis.set.call_args
        # Value should be the language code
        assert call_args.args[1] == "es"

    @pytest.mark.asyncio
    async def test_save_and_retrieve_roundtrip(self):
        stored_value = None

        async def fake_set(key, value):
            nonlocal stored_value
            stored_value = value

        async def fake_get(key):
            return stored_value.encode() if stored_value else None

        redis = AsyncMock()
        redis.set.side_effect = fake_set
        redis.get.side_effect = fake_get

        original = ChatSettings(language=Language.ES)
        await save_chat_settings(redis, chat_id=99, settings=original)

        retrieved = await get_chat_settings(redis, chat_id=99)
        assert retrieved.language == Language.ES


# ---------------------------------------------------------------------------
# Webhook: /menu command integration
# ---------------------------------------------------------------------------


class TestWebhookMenuCommand:
    def _client_with_redis(self, redis_mock=None) -> TestClient:
        app = create_app(settings=_test_settings())
        if redis_mock is None:
            redis_mock = AsyncMock()
            redis_mock.get.return_value = None  # default language
        app.state.redis = redis_mock
        return TestClient(app)

    def _menu_payload(self, chat_id: int = 1001) -> dict:
        return {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "from": {"id": 42, "first_name": "Alice"},
                "chat": {"id": chat_id, "type": "private"},
                "text": "/menu",
            },
        }

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_menu_command_returns_200(self, mock_send):
        client = self._client_with_redis()
        response = client.post("/telegram/webhook", json=self._menu_payload())
        assert response.status_code == 200
        assert response.json() == {"ok": True}

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_menu_command_calls_send_message_with_keyboard(self, mock_send):
        client = self._client_with_redis()
        client.post("/telegram/webhook", json=self._menu_payload())
        mock_send.assert_awaited_once()
        # Check that reply_markup was passed
        call_kwargs = mock_send.call_args
        assert call_kwargs.kwargs.get("reply_markup") is not None
        markup = call_kwargs.kwargs["reply_markup"]
        assert "inline_keyboard" in markup

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_menu_command_without_redis_returns_502(self, mock_send):
        app = create_app(settings=_test_settings())
        app.state.redis = None
        client = TestClient(app)
        response = client.post("/telegram/webhook", json=self._menu_payload())
        assert response.status_code == 502
        mock_send.assert_not_awaited()


# ---------------------------------------------------------------------------
# Webhook: menu callback integration
# ---------------------------------------------------------------------------


class TestWebhookMenuCallback:
    def _client_with_redis(self, redis_mock=None) -> TestClient:
        app = create_app(settings=_test_settings())
        if redis_mock is None:
            redis_mock = AsyncMock()
            redis_mock.get.return_value = None  # default language
        app.state.redis = redis_mock
        return TestClient(app)

    def _callback_payload(self, data: str, chat_id: int = 1001, message_id: int = 50) -> dict:
        return {
            "update_id": 2,
            "callback_query": {
                "id": "cbq-test",
                "from": {"id": 42, "first_name": "Alice"},
                "message": {
                    "message_id": message_id,
                    "from": {"id": 1, "first_name": "Bot"},
                    "chat": {"id": chat_id, "type": "private"},
                },
                "data": data,
            },
        }

    @patch("src.telegram.router.answer_callback_query", new_callable=AsyncMock)
    @patch("src.telegram.router.edit_message_text", new_callable=AsyncMock)
    def test_nav_callback_edits_message(self, mock_edit, mock_answer):
        client = self._client_with_redis()
        payload = self._callback_payload(build_callback("main", "nav", "language"))
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 200
        mock_edit.assert_awaited_once()
        mock_answer.assert_awaited_once()

    @patch("src.telegram.router.answer_callback_query", new_callable=AsyncMock)
    @patch("src.telegram.router.edit_message_text", new_callable=AsyncMock)
    def test_back_callback_edits_message(self, mock_edit, mock_answer):
        client = self._client_with_redis()
        payload = self._callback_payload(build_callback("language", "back", "main"))
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 200
        mock_edit.assert_awaited_once()

    @patch("src.telegram.router.answer_callback_query", new_callable=AsyncMock)
    @patch("src.telegram.router.edit_message_text", new_callable=AsyncMock)
    def test_language_set_callback_updates_language_and_edits_message(
        self, mock_edit, mock_answer
    ):
        redis_mock = AsyncMock()
        redis_mock.get.return_value = None  # language = RU
        client = self._client_with_redis(redis_mock)

        payload = self._callback_payload(build_callback("language", "set", "en"))
        response = client.post("/telegram/webhook", json=payload)

        assert response.status_code == 200
        # Language should have been saved
        redis_mock.set.assert_awaited()
        # Message should have been edited
        mock_edit.assert_awaited_once()

    @patch("src.telegram.router.answer_callback_query", new_callable=AsyncMock)
    @patch("src.telegram.router.edit_message_text", new_callable=AsyncMock)
    def test_language_set_to_ru_saves_ru(self, mock_edit, mock_answer):
        redis_mock = AsyncMock()
        redis_mock.get.return_value = b"en"
        client = self._client_with_redis(redis_mock)

        payload = self._callback_payload(build_callback("language", "set", "ru"))
        client.post("/telegram/webhook", json=payload)

        redis_mock.set.assert_awaited()
        set_call = redis_mock.set.call_args
        assert set_call.args[1] == "ru"

    @patch("src.telegram.router.answer_callback_query", new_callable=AsyncMock)
    @patch("src.telegram.router.edit_message_text", new_callable=AsyncMock)
    def test_invalid_callback_data_ignored(self, mock_edit, mock_answer):
        """Callback data that parses to None (missing parts) is ignored gracefully."""
        client = self._client_with_redis()
        payload = self._callback_payload("menu:incomplete")
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 200
        mock_edit.assert_not_awaited()

    @patch("src.telegram.router.answer_callback_query", new_callable=AsyncMock)
    @patch("src.telegram.router.edit_message_text", new_callable=AsyncMock)
    def test_settings_nav_renders_settings_stub(self, mock_edit, mock_answer):
        client = self._client_with_redis()
        payload = self._callback_payload(build_callback("main", "nav", "settings"))
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 200
        mock_edit.assert_awaited_once()
        edit_args = mock_edit.call_args
        # Text should contain settings content
        text_arg = edit_args.args[3] if len(edit_args.args) >= 4 else edit_args.kwargs.get("text", "")
        assert len(text_arg) > 0

    @patch("src.telegram.router.answer_callback_query", new_callable=AsyncMock)
    @patch("src.telegram.router.edit_message_text", new_callable=AsyncMock)
    def test_billing_nav_renders_billing_stub(self, mock_edit, mock_answer):
        client = self._client_with_redis()
        payload = self._callback_payload(build_callback("main", "nav", "billing"))
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 200
        mock_edit.assert_awaited_once()
