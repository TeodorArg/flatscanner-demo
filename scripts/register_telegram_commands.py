#!/usr/bin/env python3
"""Register localized bot commands with Telegram.

This script calls the Telegram Bot API ``setMyCommands`` endpoint to populate
the command picker with localized descriptions. Command names stay stable in
English; descriptions are registered separately for ``ru``, ``en``, and ``es``,
plus one default English scope without ``language_code``.

Usage:
    TELEGRAM_BOT_TOKEN=<token> python scripts/register_telegram_commands.py
    python scripts/register_telegram_commands.py --token <token>
"""

import argparse
import asyncio
import os
import sys

# Make the project root importable when running this script directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx  # noqa: E402

from src.i18n.types import Language  # noqa: E402
from src.telegram.menu.commands import get_bot_commands  # noqa: E402

_TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}"

# Map Language enum values to Telegram language_code strings.
_LANG_CODES: dict[Language, str] = {
    Language.RU: "ru",
    Language.EN: "en",
    Language.ES: "es",
}


async def register_commands(token: str) -> None:
    """Push command definitions to Telegram for all supported language scopes."""
    base = _TELEGRAM_API_BASE.format(token=token)
    async with httpx.AsyncClient(timeout=15) as client:
        for lang, lang_code in _LANG_CODES.items():
            commands = get_bot_commands(lang)
            payload = {"commands": commands, "language_code": lang_code}
            response = await client.post(f"{base}/setMyCommands", json=payload)
            response.raise_for_status()
            print(
                f"[OK] Registered {len(commands)} commands for language_code={lang_code!r}"
            )

        default_commands = get_bot_commands(Language.EN)
        response = await client.post(
            f"{base}/setMyCommands",
            json={"commands": default_commands},
        )
        response.raise_for_status()
        print(
            "[OK] Registered "
            f"{len(default_commands)} commands as default (no language_code)"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register Telegram bot commands for all supported language scopes."
    )
    parser.add_argument(
        "--token",
        help="Telegram bot token. Overrides the TELEGRAM_BOT_TOKEN environment variable.",
    )
    args = parser.parse_args()

    token = args.token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print(
            "Error: bot token is required. Pass --token or set TELEGRAM_BOT_TOKEN.",
            file=sys.stderr,
        )
        sys.exit(1)

    asyncio.run(register_commands(token))


if __name__ == "__main__":
    main()
