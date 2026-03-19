# Plan: Telegram Menu, Settings, and Billing Foundation

## Summary

Introduce a minimal inline-menu UX for Telegram that gives the bot a durable
navigation model for language switching, future settings, and future billing.
The implementation should separate menu rendering, callback parsing, chat
settings persistence, and billing-domain placeholders so the Telegram layer can
grow without devolving into command-specific branches.

## Architecture Direction

- Add a screen-based Telegram menu layer driven by inline keyboards
- Add a compact callback schema such as `menu:<screen>:<action>:<value?>`
- Introduce a generalized `ChatSettings` model and repository
- Migrate language preference reads/writes behind the new settings repository
- Keep `/language` as a fallback command, but make the menu-driven language
  flow the primary UX
- Add stub settings and billing screens with stable screen IDs and copy coming
  from i18n
- Keep billing logic behind a domain boundary so the first real payment
  implementation can plug in later without rewriting the menu system

## Files And Areas

- `src/telegram/`
- `src/storage/`
- `src/i18n/`
- `src/domain/`
- `tests/`
- `specs/013-telegram-menu-settings-billing-foundation/`

## Risks

- If callback parsing is implemented ad hoc in `router.py`, future menu growth
  will become brittle quickly
- If settings stay split across one-off Redis keys, adding more user
  preferences will create storage and migration debt
- If billing UI is coupled directly to provider-specific payment code, the menu
  will become hard to evolve
- If the menu is too heavy or noisy, the bot UX will regress on mobile

## Validation

- Add callback parsing tests for main-menu and sub-screen actions
- Add rendering tests for localized main menu, language screen, settings screen,
  and billing screen
- Add persistence tests for generalized chat settings and language writes
- Add webhook/Telegram integration tests for `/menu` and menu-based language
  selection
- Run `python -m pytest -q`

## Planned Slices

1. Menu foundation
   - `/menu`
   - callback schema
   - main menu
   - language screen
   - generalized `ChatSettings`
2. Settings and billing stubs
   - settings screen shell
   - billing screen shell
   - navigation polish
3. Follow-on product work
   - first real settings toggles
   - billing products, plans, and payment integration
