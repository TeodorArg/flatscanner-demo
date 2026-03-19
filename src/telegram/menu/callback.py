"""Inline-keyboard callback payload schema and parser.

All callback data produced by the menu system follows the compact schema::

    menu:<screen>:<action>:<value>

Where:

- ``screen`` — the menu screen that produced the button (e.g. ``main``,
  ``language``, ``settings``, ``billing``, ``help``).
- ``action`` — the operation to perform:
  - ``nav``  — navigate forward to ``value`` screen
  - ``back`` — navigate back to ``value`` screen (usually ``main``)
  - ``set``  — apply a setting value to the current screen
- ``value`` — target screen name (for ``nav``/``back``) or a setting value
  such as a language code (for ``set``).

Examples::

    menu:main:nav:language   # main menu → language screen
    menu:language:set:en     # language screen → set language to EN
    menu:language:back:main  # language screen → back to main menu
    menu:settings:back:main  # settings screen → back to main menu
    menu:billing:back:main   # billing screen → back to main menu
"""

from __future__ import annotations

from dataclasses import dataclass

_PREFIX = "menu"
_SEP = ":"
_PARTS = 4  # prefix + screen + action + value


@dataclass(frozen=True)
class MenuCallback:
    screen: str
    action: str
    value: str


def build_callback(screen: str, action: str, value: str) -> str:
    """Return a callback_data string for the given screen/action/value."""
    return f"{_PREFIX}{_SEP}{screen}{_SEP}{action}{_SEP}{value}"


def parse_callback(data: str) -> MenuCallback | None:
    """Parse a callback_data string and return a :class:`MenuCallback`.

    Returns ``None`` if *data* is not a valid menu callback payload.
    """
    parts = data.split(_SEP, _PARTS - 1)
    if len(parts) != _PARTS or parts[0] != _PREFIX:
        return None
    _, screen, action, value = parts
    if not screen or not action or not value:
        return None
    return MenuCallback(screen=screen, action=action, value=value)


def is_menu_callback(data: str) -> bool:
    """Return ``True`` if *data* looks like a menu callback payload."""
    return data.startswith(f"{_PREFIX}{_SEP}")
