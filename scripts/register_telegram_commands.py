#!/usr/bin/env python3
"""Register bot commands with Telegram for all supported language scopes.

This script calls the Telegram Bot API ``setMyCommands`` endpoint to populate
the command picker with localized descriptions.  Command names are always
English; descriptions are registered separately for ``ru``, ``en``, and ``es``
language scopes, plus one default scope (English, no language_code) for users
whose Telegram client language is not explicitly supported.

Usage::

    # Using an environment variable:
    TELEGRAM_BOT_TOKEN=<token> python scripts/register_telegram_commands.py

    # Passing the token directly:
    python scripts/register_telegram_commands.py --token <token>

Requirements:
    httpx must be installed (it is part of the project's runtime dependencies).
"""

import argparse
import asyncio
import os
import sys

# Make the project root importable when running this script directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx  # noqa: E402 — must come after sys.path adjustment

from src.i18n.types import Language  # noqa: E402
from src.telegram.menu.commands import get_bot_commands  # noqa: E402

_TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}"

# Map Language enum value → Telegram language_code string.
_LANG_CODES: dict[Language, str] = {
    Language.RU: "ru",
    Language.EN: "en",
    Language.ES: "es",
}


async def register_commands(token: str) -> None:
    """Push command definitions to Telegram for all supported language scopes."""
    base = _TELEGRAM_API_BASE.format(token=token)
    async with httpx.AsyncClient(timeout=15) as client:
        # Register per-language scoped commands.
        for lang, lang_code in _LANG_CODES.items():
            commands = get_bot_commands(lang)
            payload = {"commands": commands, "language_code": lang_code}
            resp = await client.post(f"{base}/setMyCommands", json=payload)
            resp.raise_for_status()
            print(f"[OK] Registered {len(commands)} commands for language_code={lang_code!r}")

        # Register English commands as the default fallback (no language_code).
        en_commands = get_bot_commands(Language.EN)
        resp = await client.post(f"{base}/setMyCommands", json={"commands": en_commands})
        resp.raise_for_status()
        print(f"[OK] Registered {len(en_commands)} commands as default (no language_code)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register Telegram bot commands for all supported language scopes."
    )
    parser.add_argument(
        "--token",
        help="Telegram bot token.  Overrides the TELEGRAM_BOT_TOKEN environment variable.",
    )
    args = parser.parse_args()

    token = args.token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print(
            "Error: bot token is required.  Pass --token or set TELEGRAM_BOT_TOKEN.",
            file=sys.stderr,
        )
        sys.exit(1)

    asyncio.run(register_commands(token))


if __name__ == "__main__":
    main()
