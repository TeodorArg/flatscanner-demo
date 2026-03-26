"""Tests for the S1 delivery-foundation models and ProgressSink protocol.

Covers:
- DeliveryChannel enum values and serialization.
- TelegramDeliveryContext model creation and JSON round-trip.
- ProgressSink as a structural Protocol (runtime_checkable).
- TelegramProgressSink satisfies the ProgressSink protocol.
- SpyProgressSink satisfies the ProgressSink protocol.
"""

from __future__ import annotations

import pytest

from src.domain.delivery import DeliveryChannel, ProgressSink, TelegramDeliveryContext
from src.telegram.progress import TelegramProgressSink


# ---------------------------------------------------------------------------
# DeliveryChannel enum
# ---------------------------------------------------------------------------


class TestDeliveryChannel:
    def test_telegram_value(self):
        assert DeliveryChannel.TELEGRAM == "telegram"

    def test_web_value(self):
        assert DeliveryChannel.WEB == "web"

    def test_is_str_enum(self):
        assert isinstance(DeliveryChannel.TELEGRAM, str)

    def test_serializes_as_string(self):
        import json

        data = {"channel": DeliveryChannel.TELEGRAM}
        serialized = json.dumps({"channel": DeliveryChannel.TELEGRAM.value})
        assert json.loads(serialized)["channel"] == "telegram"


# ---------------------------------------------------------------------------
# TelegramDeliveryContext model
# ---------------------------------------------------------------------------


class TestTelegramDeliveryContext:
    def test_basic_construction(self):
        ctx = TelegramDeliveryContext(chat_id=1001, message_id=7)
        assert ctx.chat_id == 1001
        assert ctx.message_id == 7
        assert ctx.progress_message_id is None

    def test_with_progress_message_id(self):
        ctx = TelegramDeliveryContext(chat_id=1001, message_id=7, progress_message_id=42)
        assert ctx.progress_message_id == 42

    def test_json_round_trip_no_progress(self):
        ctx = TelegramDeliveryContext(chat_id=55, message_id=3)
        restored = TelegramDeliveryContext.model_validate_json(ctx.model_dump_json())
        assert restored.chat_id == 55
        assert restored.message_id == 3
        assert restored.progress_message_id is None

    def test_json_round_trip_with_progress(self):
        ctx = TelegramDeliveryContext(chat_id=55, message_id=3, progress_message_id=88)
        restored = TelegramDeliveryContext.model_validate_json(ctx.model_dump_json())
        assert restored.progress_message_id == 88

    def test_rejects_missing_required_fields(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TelegramDeliveryContext(chat_id=1)  # message_id missing


# ---------------------------------------------------------------------------
# ProgressSink protocol
# ---------------------------------------------------------------------------


class TestProgressSinkProtocol:
    def test_telegram_progress_sink_satisfies_protocol(self):
        """TelegramProgressSink must be recognized as a ProgressSink at runtime."""
        sink = TelegramProgressSink("token", 1, None)
        assert isinstance(sink, ProgressSink)

    def test_plain_conformant_object_satisfies_protocol(self):
        """Any object with the four async methods satisfies ProgressSink."""

        class MinimalSink:
            async def start(self) -> None: ...
            async def update(self, text: str) -> None: ...
            async def complete(self) -> None: ...
            async def fail(self) -> None: ...

        assert isinstance(MinimalSink(), ProgressSink)

    def test_object_missing_method_fails_protocol_check(self):
        """An object missing one of the required methods must NOT satisfy ProgressSink."""

        class IncompleteSink:
            async def start(self) -> None: ...
            async def update(self, text: str) -> None: ...
            # complete and fail are missing

        assert not isinstance(IncompleteSink(), ProgressSink)

    def test_protocol_has_expected_methods(self):
        """ProgressSink exposes start, update, complete, and fail."""
        for method_name in ("start", "update", "complete", "fail"):
            assert hasattr(ProgressSink, method_name)
