"""Tests for Telegram bot entrypoints and message routing."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import redis.asyncio as aioredis
from fastapi.testclient import TestClient

from src.app.config import Settings
from src.app.main import create_app
from src.domain.listing import ListingProvider
from src.telegram.dispatcher import extract_url, extract_urls, is_supported_provider, route_update
from src.telegram.models import TelegramChat, TelegramMessage, TelegramUpdate, TelegramUser
from src.telegram.sender import send_message


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


def _make_caption_update(
    caption: str | None,
    chat_id: int = 1001,
    update_id: int = 1,
) -> TelegramUpdate:
    """Build a TelegramUpdate with no text body but a media caption."""
    user = TelegramUser(id=42, first_name="Alice")
    chat = TelegramChat(id=chat_id, type="private")
    message = TelegramMessage(
        message_id=1,
        **{"from": user},
        chat=chat,
        text=None,
        caption=caption,
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
# extract_urls
# ---------------------------------------------------------------------------


class TestExtractUrls:
    def test_returns_empty_list_when_no_url(self):
        assert extract_urls("Hello, how are you?") == []

    def test_returns_single_url(self):
        assert extract_urls("See https://airbnb.com/rooms/1") == ["https://airbnb.com/rooms/1"]

    def test_returns_all_urls(self):
        text = "https://booking.com/hotel/x and https://airbnb.com/rooms/1"
        assert extract_urls(text) == ["https://booking.com/hotel/x", "https://airbnb.com/rooms/1"]

    def test_strips_trailing_punctuation_from_each_url(self):
        text = "Check https://airbnb.com/rooms/1. Also https://example.com/flat,"
        result = extract_urls(text)
        assert result == ["https://airbnb.com/rooms/1", "https://example.com/flat"]

    def test_empty_string_returns_empty_list(self):
        assert extract_urls("") == []


# ---------------------------------------------------------------------------
# is_supported_provider
# ---------------------------------------------------------------------------


class TestIsSupportedProvider:
    def test_airbnb_com_is_supported(self):
        assert is_supported_provider("https://www.airbnb.com/rooms/123") is True

    def test_airbnb_apex_domain_is_supported(self):
        assert is_supported_provider("https://airbnb.com/rooms/123") is True

    def test_airbnb_country_subdomain_is_supported(self):
        assert is_supported_provider("https://www.airbnb.co.uk/rooms/123") is True

    def test_airbnb_localized_apex_domain_is_supported(self):
        assert is_supported_provider("https://airbnb.co.uk/rooms/456") is True

    def test_airbnb_ccTLD_is_supported(self):
        assert is_supported_provider("https://www.airbnb.de/rooms/789") is True

    def test_airbnb_ru_is_supported(self):
        assert is_supported_provider("https://www.airbnb.ru/rooms/789") is True

    def test_airbnb_compound_ccTLD_com_au_is_supported(self):
        assert is_supported_provider("https://www.airbnb.com.au/rooms/1") is True

    def test_airbnb_generic_tld_is_supported(self):
        assert is_supported_provider("https://www.airbnb.xyz/rooms/1") is True

    def test_airbnb_localized_non_listing_page_is_not_supported(self):
        assert is_supported_provider("https://www.airbnb.co.uk/help/article/1") is False

    def test_airbnb_lookalike_with_extra_segment_not_supported(self):
        # airbnb.evil.com — airbnb is a subdomain of evil.com, not the SLD
        assert is_supported_provider("https://airbnb.evil.com/rooms/1") is False

    def test_booking_com_is_not_supported(self):
        assert is_supported_provider("https://www.booking.com/hotel/1") is False

    def test_example_com_is_not_supported(self):
        assert is_supported_provider("https://example.com/flat") is False

    def test_airbnb_look_alike_is_not_supported(self):
        # hostname doesn't end with .airbnb.com and isn't airbnb.com
        assert is_supported_provider("https://notairbnb.com/rooms/1") is False

    def test_abnb_me_short_link_is_supported(self):
        assert is_supported_provider("https://abnb.me/abc123") is True

    def test_abnb_me_subdomain_is_supported(self):
        assert is_supported_provider("https://www.abnb.me/abc123") is True

    def test_abnb_me_look_alike_is_not_supported(self):
        assert is_supported_provider("https://notabnb.me/abc123") is False

    def test_airbnb_help_page_is_not_supported(self):
        # Non-listing Airbnb pages must not trigger an analysis job
        assert is_supported_provider("https://www.airbnb.com/help/article/2701") is False

    def test_airbnb_search_url_is_not_supported(self):
        assert is_supported_provider("https://www.airbnb.com/s/Paris--France") is False

    def test_airbnb_home_page_is_not_supported(self):
        assert is_supported_provider("https://www.airbnb.com/") is False

    def test_airbnb_listing_rooms_path_is_supported(self):
        assert is_supported_provider("https://www.airbnb.com/rooms/12345678") is True

    # --- Malformed /rooms/ paths ---

    def test_airbnb_bare_rooms_path_is_not_supported(self):
        # /rooms/ with no listing ID must not trigger analysis
        assert is_supported_provider("https://www.airbnb.com/rooms/") is False

    def test_airbnb_rooms_path_no_trailing_slash_is_not_supported(self):
        # /rooms with no slash or ID must not trigger analysis
        assert is_supported_provider("https://www.airbnb.com/rooms") is False

    # --- Malformed abnb.me paths ---

    def test_abnb_me_root_path_is_not_supported(self):
        # https://abnb.me/ with no share code must not trigger analysis
        assert is_supported_provider("https://abnb.me/") is False

    def test_abnb_me_no_path_is_not_supported(self):
        # https://abnb.me with no path at all must not trigger analysis
        assert is_supported_provider("https://abnb.me") is False

    def test_airbnb_rooms_path_with_extra_segment_is_not_supported(self):
        # /rooms/123/photos is not a canonical listing URL — extra segments must be rejected
        assert is_supported_provider("https://www.airbnb.com/rooms/123/photos") is False

    # --- Bogus hosts outside the generic Airbnb hostname shape ---

    def test_airbnb_long_fake_suffix_is_not_supported(self):
        # www.airbnb.notreal does not match the 1-2 label TLD pattern
        assert is_supported_provider("https://www.airbnb.notreal/rooms/123") is False

    # --- Non-http/https schemes ---

    def test_ftp_scheme_is_not_supported(self):
        # ftp:// must be rejected regardless of host
        assert is_supported_provider("ftp://airbnb.com/rooms/123") is False

    def test_javascript_scheme_is_not_supported(self):
        # javascript: URIs must never be accepted
        assert is_supported_provider("javascript://airbnb.com/rooms/123") is False

    def test_file_scheme_is_not_supported(self):
        # file:// URIs must be rejected
        assert is_supported_provider("file:///airbnb.com/rooms/123") is False


# ---------------------------------------------------------------------------
# route_update
# ---------------------------------------------------------------------------


class TestRouteUpdate:
    def test_analyse_when_airbnb_url(self):
        update = _make_update("https://www.airbnb.com/rooms/999", chat_id=5)
        decision = route_update(update)
        assert decision["action"] == "analyse"
        assert decision["url"] == "https://www.airbnb.com/rooms/999"
        assert decision["chat_id"] == 5

    def test_analyse_when_abnb_me_short_link(self):
        update = _make_update("https://abnb.me/abc123", chat_id=6)
        decision = route_update(update)
        assert decision["action"] == "analyse"
        assert decision["url"] == "https://abnb.me/abc123"
        assert decision["chat_id"] == 6

    def test_analyse_decision_includes_provider(self):
        update = _make_update("https://www.airbnb.com/rooms/999", chat_id=5)
        decision = route_update(update)
        assert decision["action"] == "analyse"
        assert decision["provider"] == ListingProvider.AIRBNB

    def test_unsupported_when_non_airbnb_url(self):
        update = _make_update("https://www.booking.com/hotel/xyz", chat_id=9)
        decision = route_update(update)
        assert decision["action"] == "unsupported"
        assert decision["url"] == "https://www.booking.com/hotel/xyz"
        assert decision["chat_id"] == 9

    def test_unsupported_when_generic_url(self):
        update = _make_update("https://example.com/flat/42", chat_id=11)
        decision = route_update(update)
        assert decision["action"] == "unsupported"
        assert decision["chat_id"] == 11

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

    def test_analyse_when_supported_url_follows_unsupported(self):
        """Router must find the supported URL even when it is not the first URL."""
        update = _make_update(
            "try https://www.booking.com/hotel/xyz or https://www.airbnb.com/rooms/123",
            chat_id=5,
        )
        decision = route_update(update)
        assert decision["action"] == "analyse"
        assert decision["url"] == "https://www.airbnb.com/rooms/123"
        assert decision["chat_id"] == 5

    def test_unsupported_when_all_urls_are_unsupported(self):
        """When multiple URLs are present but none is supported, report the first."""
        update = _make_update(
            "https://www.booking.com/hotel/abc or https://example.com/flat",
            chat_id=9,
        )
        decision = route_update(update)
        assert decision["action"] == "unsupported"
        assert decision["url"] == "https://www.booking.com/hotel/abc"


# ---------------------------------------------------------------------------
# Caption-based routing
# ---------------------------------------------------------------------------


class TestCaptionRouting:
    """Airbnb links in media captions must route identically to text messages."""

    def test_analyse_when_airbnb_url_in_caption(self):
        update = _make_caption_update("https://www.airbnb.com/rooms/999", chat_id=5)
        decision = route_update(update)
        assert decision["action"] == "analyse"
        assert decision["url"] == "https://www.airbnb.com/rooms/999"
        assert decision["chat_id"] == 5

    def test_analyse_when_abnb_me_url_in_caption(self):
        update = _make_caption_update("https://abnb.me/abc123", chat_id=6)
        decision = route_update(update)
        assert decision["action"] == "analyse"
        assert decision["url"] == "https://abnb.me/abc123"

    def test_unsupported_when_non_airbnb_url_in_caption(self):
        update = _make_caption_update("https://www.booking.com/hotel/xyz", chat_id=9)
        decision = route_update(update)
        assert decision["action"] == "unsupported"

    def test_help_when_caption_has_no_url(self):
        update = _make_caption_update("Nice place!", chat_id=7)
        decision = route_update(update)
        assert decision["action"] == "help"

    def test_ignore_when_caption_is_none(self):
        update = _make_caption_update(caption=None)
        decision = route_update(update)
        assert decision["action"] == "ignore"

    def test_text_takes_precedence_over_caption(self):
        """If a message has both text and caption, text should drive routing."""
        user = TelegramUser(id=42, first_name="Alice")
        chat = TelegramChat(id=5, type="private")
        message = TelegramMessage(
            message_id=1,
            **{"from": user},
            chat=chat,
            text="https://www.airbnb.com/rooms/111",
            caption="https://www.booking.com/hotel/xyz",
        )
        update = TelegramUpdate(update_id=1, message=message)
        decision = route_update(update)
        assert decision["action"] == "analyse"
        assert decision["url"] == "https://www.airbnb.com/rooms/111"


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
        app = create_app(settings=_test_settings(**settings_overrides))
        mock_redis = AsyncMock()
        mock_redis.eval.return_value = 1  # enqueue_analysis_job succeeds
        app.state.redis = mock_redis
        return TestClient(app)

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

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_webhook_url_with_query_params_echoed_correctly(self, mock_send):
        """URLs containing & query params must be echoed verbatim (no HTML escaping)."""
        url_with_params = "https://www.airbnb.com/rooms/123?check_in=2024-01-01&check_out=2024-01-05&guests=2"
        client = self._client()
        payload = self._update_payload(url_with_params, chat_id=1001)
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        call_args = mock_send.call_args[0]
        # Full URL including query string must appear verbatim in the reply text
        assert url_with_params in call_args[2]

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_webhook_unsupported_url_sends_unsupported_reply(self, mock_send):
        client = self._client()
        payload = self._update_payload("https://www.booking.com/hotel/xyz", chat_id=1001)
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        mock_send.assert_awaited_once()
        call_args = mock_send.call_args[0]
        assert call_args[1] == 1001
        # Must not claim analysis has started
        assert "looking at" not in call_args[2]
        assert "support" in call_args[2].lower() or "provider" in call_args[2].lower()

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_webhook_returns_non_2xx_when_send_message_raises(self, mock_send):
        """Network / unexpected failures must return non-2xx so Telegram retries."""
        mock_send.side_effect = Exception("network failure")
        client = self._client()
        payload = self._update_payload("https://airbnb.com/rooms/1")
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code >= 400

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_webhook_returns_502_on_5xx_telegram_error(self, mock_send):
        """5xx Telegram errors are transient — webhook must return 502 to trigger retry."""
        mock_send.side_effect = httpx.HTTPStatusError(
            "503 Service Unavailable",
            request=httpx.Request("POST", "https://api.telegram.org/bottoken/sendMessage"),
            response=httpx.Response(503),
        )
        client = self._client()
        payload = self._update_payload("https://airbnb.com/rooms/1")
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 502

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_webhook_returns_200_on_4xx_telegram_error(self, mock_send):
        """Permanent 4xx Telegram errors must be acknowledged (200) to avoid retry loops."""
        mock_send.side_effect = httpx.HTTPStatusError(
            "400 Bad Request",
            request=httpx.Request("POST", "https://api.telegram.org/bottoken/sendMessage"),
            response=httpx.Response(400),
        )
        client = self._client()
        payload = self._update_payload("https://airbnb.com/rooms/1")
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 200
        assert response.json() == {"ok": True}

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_webhook_returns_200_on_403_telegram_error(self, mock_send):
        """403 from Telegram (bot blocked) is permanent — must acknowledge and not retry."""
        mock_send.side_effect = httpx.HTTPStatusError(
            "403 Forbidden",
            request=httpx.Request("POST", "https://api.telegram.org/bottoken/sendMessage"),
            response=httpx.Response(403),
        )
        client = self._client()
        payload = self._update_payload("https://airbnb.com/rooms/1")
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 200

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_webhook_returns_502_on_429_telegram_error(self, mock_send):
        """429 Too Many Requests is transient — webhook must return 502 so Telegram retries."""
        mock_send.side_effect = httpx.HTTPStatusError(
            "429 Too Many Requests",
            request=httpx.Request("POST", "https://api.telegram.org/bottoken/sendMessage"),
            response=httpx.Response(429),
        )
        client = self._client()
        payload = self._update_payload("https://airbnb.com/rooms/1")
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 502

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_webhook_caption_airbnb_url_triggers_analyse_reply(self, mock_send):
        """An Airbnb URL in a media caption must route to analysis just like message text."""
        client = self._client()
        payload = {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "from": {"id": 42, "first_name": "Alice"},
                "chat": {"id": 1001, "type": "private"},
                "caption": "https://www.airbnb.com/rooms/456",
            },
        }
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        mock_send.assert_awaited_once()
        call_args = mock_send.call_args[0]
        assert call_args[1] == 1001
        assert "airbnb.com/rooms/456" in call_args[2]

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_webhook_analyse_returns_502_when_redis_unavailable(self, mock_send):
        """When Redis is unavailable, the analyse path must return 502 and not send a false acknowledgement."""
        app = create_app(settings=_test_settings())
        # app.state.redis is None by default (lifespan not run)
        client = TestClient(app)
        payload = self._update_payload("https://www.airbnb.com/rooms/123")
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 502
        mock_send.assert_not_awaited()

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_webhook_analyse_returns_502_on_redis_error_during_enqueue(self, mock_send):
        """A RedisError raised by enqueue_analysis_job must return 502 and not call send_message."""
        app = create_app(settings=_test_settings())
        mock_redis = AsyncMock()
        mock_redis.eval.side_effect = aioredis.RedisError("connection reset")
        app.state.redis = mock_redis
        client = TestClient(app)
        payload = self._update_payload("https://www.airbnb.com/rooms/123")
        response = client.post("/telegram/webhook", json=payload)
        assert response.status_code == 502
        mock_send.assert_not_awaited()


# ---------------------------------------------------------------------------
# Webhook authentication
# ---------------------------------------------------------------------------


class TestWebhookAuthentication:
    def _client(self, **settings_overrides) -> TestClient:
        app = create_app(settings=_test_settings(**settings_overrides))
        mock_redis = AsyncMock()
        mock_redis.eval.return_value = 1
        app.state.redis = mock_redis
        return TestClient(app)

    def _update_payload(self) -> dict:
        return {
            "update_id": 1,
            "message": {
                "message_id": 1,
                "from": {"id": 42, "first_name": "Alice"},
                "chat": {"id": 1001, "type": "private"},
                "text": "https://airbnb.com/rooms/1",
            },
        }

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_no_secret_configured_accepts_request_without_header(self, mock_send):
        """When no webhook secret is configured any request is accepted."""
        client = self._client()  # telegram_webhook_secret defaults to ""
        response = client.post("/telegram/webhook", json=self._update_payload())
        assert response.status_code == 200

    @patch("src.telegram.router.send_message", new_callable=AsyncMock)
    def test_correct_secret_header_accepted(self, mock_send):
        client = self._client(telegram_webhook_secret="correct-secret")
        response = client.post(
            "/telegram/webhook",
            json=self._update_payload(),
            headers={"X-Telegram-Bot-Api-Secret-Token": "correct-secret"},
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_missing_secret_header_rejected(self):
        client = self._client(telegram_webhook_secret="correct-secret")
        response = client.post("/telegram/webhook", json=self._update_payload())
        assert response.status_code == 403

    def test_wrong_secret_header_rejected(self):
        client = self._client(telegram_webhook_secret="correct-secret")
        response = client.post(
            "/telegram/webhook",
            json=self._update_payload(),
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
        )
        assert response.status_code == 403

    def test_invalid_body_with_wrong_secret_returns_403_not_422(self):
        """Auth rejection must occur before schema validation (bad body + wrong secret → 403)."""
        client = self._client(telegram_webhook_secret="correct-secret")
        response = client.post(
            "/telegram/webhook",
            json={"bad": "data"},
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# send_message non-2xx behaviour
# ---------------------------------------------------------------------------


class TestSendMessage:
    @pytest.mark.asyncio
    async def test_raises_on_non_2xx_response(self):
        """send_message must propagate an HTTPStatusError on non-2xx Telegram responses."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request",
            request=httpx.Request("POST", "https://api.telegram.org/bottoken/sendMessage"),
            response=httpx.Response(400),
        )
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await send_message("token", 123, "hello", client=mock_client)

    @pytest.mark.asyncio
    async def test_does_not_raise_on_2xx_response(self):
        """send_message must not raise when the Telegram API returns 2xx."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        # Should complete without raising
        await send_message("token", 123, "hello", client=mock_client)
        mock_client.post.assert_awaited_once()
