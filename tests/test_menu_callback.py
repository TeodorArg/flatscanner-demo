"""Tests for the menu callback payload schema."""

from __future__ import annotations

import pytest

from src.telegram.menu.callback import (
    MenuCallback,
    build_callback,
    is_menu_callback,
    parse_callback,
)


class TestBuildCallback:
    def test_produces_expected_format(self):
        assert build_callback("main", "nav", "language") == "menu:main:nav:language"

    def test_produces_set_action(self):
        assert build_callback("language", "set", "en") == "menu:language:set:en"

    def test_produces_back_action(self):
        assert build_callback("language", "back", "main") == "menu:language:back:main"

    def test_billing_back(self):
        assert build_callback("billing", "back", "main") == "menu:billing:back:main"


class TestParseCallback:
    def test_parses_nav_payload(self):
        result = parse_callback("menu:main:nav:language")
        assert result == MenuCallback(screen="main", action="nav", value="language")

    def test_parses_set_payload(self):
        result = parse_callback("menu:language:set:ru")
        assert result == MenuCallback(screen="language", action="set", value="ru")

    def test_parses_back_payload(self):
        result = parse_callback("menu:language:back:main")
        assert result == MenuCallback(screen="language", action="back", value="main")

    def test_returns_none_for_wrong_prefix(self):
        assert parse_callback("action:main:nav:language") is None

    def test_returns_none_for_too_few_parts(self):
        assert parse_callback("menu:main:nav") is None

    def test_returns_none_for_empty_string(self):
        assert parse_callback("") is None

    def test_returns_none_for_plain_text(self):
        assert parse_callback("hello world") is None

    def test_returns_none_for_extra_colons_in_prefix(self):
        # "menu:x:y:z:extra" — the split(sep, 3) produces 4 parts so it succeeds;
        # the value includes the extra segment.
        result = parse_callback("menu:main:nav:language:extra")
        assert result is not None
        assert result.value == "language:extra"

    def test_roundtrip_build_then_parse(self):
        for screen, action, value in [
            ("main", "nav", "settings"),
            ("language", "set", "es"),
            ("billing", "back", "main"),
        ]:
            data = build_callback(screen, action, value)
            parsed = parse_callback(data)
            assert parsed == MenuCallback(screen=screen, action=action, value=value)


class TestIsMenuCallback:
    def test_returns_true_for_menu_prefix(self):
        assert is_menu_callback("menu:main:nav:language") is True

    def test_returns_false_for_other_prefix(self):
        assert is_menu_callback("action:main:nav:language") is False

    def test_returns_false_for_empty_string(self):
        assert is_menu_callback("") is False

    def test_returns_false_for_plain_text(self):
        assert is_menu_callback("hello") is False

    def test_returns_true_for_any_menu_payload(self):
        for payload in [
            build_callback("main", "nav", "language"),
            build_callback("language", "set", "en"),
            build_callback("settings", "back", "main"),
        ]:
            assert is_menu_callback(payload) is True
