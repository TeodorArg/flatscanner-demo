"""Tests for Telegram command-definition payload generation."""

from __future__ import annotations

import pytest

from src.i18n.types import Language
from src.telegram.menu.commands import COMMAND_ORDER, get_bot_commands

# Expected command names (stable English identifiers).
_EXPECTED_COMMANDS = {"menu", "language", "settings", "billing", "help"}


class TestGetBotCommandsStructure:
    def test_returns_all_five_commands_for_english(self):
        commands = get_bot_commands(Language.EN)
        assert len(commands) == 5

    def test_returns_all_five_commands_for_russian(self):
        commands = get_bot_commands(Language.RU)
        assert len(commands) == 5

    def test_returns_all_five_commands_for_spanish(self):
        commands = get_bot_commands(Language.ES)
        assert len(commands) == 5

    def test_each_entry_has_command_and_description_keys(self):
        for lang in Language:
            for entry in get_bot_commands(lang):
                assert "command" in entry
                assert "description" in entry

    def test_command_names_are_always_english(self):
        for lang in Language:
            names = {entry["command"] for entry in get_bot_commands(lang)}
            assert names == _EXPECTED_COMMANDS

    def test_command_order_matches_command_order_constant(self):
        commands = get_bot_commands(Language.EN)
        assert [c["command"] for c in commands] == COMMAND_ORDER

    def test_descriptions_are_non_empty_strings(self):
        for lang in Language:
            for entry in get_bot_commands(lang):
                assert isinstance(entry["description"], str)
                assert len(entry["description"]) > 0


class TestGetBotCommandsLocalization:
    def test_english_descriptions_are_in_english(self):
        commands = {c["command"]: c["description"] for c in get_bot_commands(Language.EN)}
        assert "menu" in commands["menu"].lower() or "main" in commands["menu"].lower()
        assert "language" in commands["language"].lower() or "change" in commands["language"].lower()
        assert "settings" in commands["settings"].lower()
        assert "billing" in commands["billing"].lower() or "plan" in commands["billing"].lower()
        assert "help" in commands["help"].lower()

    def test_russian_descriptions_are_in_russian(self):
        commands = {c["command"]: c["description"] for c in get_bot_commands(Language.RU)}
        # Russian descriptions contain Cyrillic characters.
        for name, desc in commands.items():
            assert any("\u0400" <= ch <= "\u04ff" for ch in desc), (
                f"Russian description for {name!r} has no Cyrillic characters: {desc!r}"
            )

    def test_spanish_descriptions_differ_from_english(self):
        en = {c["command"]: c["description"] for c in get_bot_commands(Language.EN)}
        es = {c["command"]: c["description"] for c in get_bot_commands(Language.ES)}
        # At least one command should have a different description.
        assert any(en[name] != es[name] for name in _EXPECTED_COMMANDS)

    def test_descriptions_differ_across_languages(self):
        ru = {c["command"]: c["description"] for c in get_bot_commands(Language.RU)}
        en = {c["command"]: c["description"] for c in get_bot_commands(Language.EN)}
        es = {c["command"]: c["description"] for c in get_bot_commands(Language.ES)}
        # All three languages should produce at least one distinct description set.
        all_same = all(ru[n] == en[n] == es[n] for n in _EXPECTED_COMMANDS)
        assert not all_same

    def test_command_names_are_lowercase_ascii(self):
        for entry in get_bot_commands(Language.EN):
            name = entry["command"]
            assert name == name.lower()
            assert name.isascii()


class TestCommandOrderConstant:
    def test_command_order_contains_all_required_commands(self):
        assert set(COMMAND_ORDER) == _EXPECTED_COMMANDS

    def test_command_order_has_no_duplicates(self):
        assert len(COMMAND_ORDER) == len(set(COMMAND_ORDER))

    def test_menu_comes_first(self):
        assert COMMAND_ORDER[0] == "menu"
