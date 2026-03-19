# Tasks: Telegram Menu, Settings, and Billing Foundation

## Spec

- [x] Define inline-menu navigation as the primary Telegram UX
- [x] Record the generalized `ChatSettings` direction for language and future
  preferences
- [x] Capture billing as a domain boundary plus UI entry point, not a payment
  provider implementation in this feature

## Design

- [x] Define the first screen set: main, language, settings, billing, help
- [x] Define a stable callback payload schema for menu navigation and selection
- [x] Define how `/menu` and `/language` coexist during the transition
- [x] Define the minimal UX style: compact inline keyboards, one primary menu
  message, concise copy

## Implementation

- [x] Add Telegram menu callback parsing and screen rendering foundation
  (`src/telegram/menu/callback.py`, `src/telegram/menu/screens.py`)
- [x] Add `/menu` command handling (dispatcher + router)
- [x] Add main menu inline keyboard and localized copy
- [x] Introduce generalized `ChatSettings` storage and migrate language access
  (`src/storage/chat_settings.py` wraps `chat_preferences`)
- [x] Add menu-based language selection screen
- [x] Keep `/language` fallback behavior working on top of the settings layer
- [x] Add stub settings screen designed for future options
- [x] Add stub billing screen designed for future plans and checkout flows
- [x] Add i18n strings for menu labels, buttons, and navigation feedback
  (all `menu.*` keys added to `src/i18n/catalog.py`)
- [x] Add command entry points for `/settings`, `/billing`, and `/help`
- [x] Register Telegram command picker entries for `menu`, `language`,
  `settings`, `billing`, and `help`
- [x] Add localized command descriptions for `ru`, `en`, and `es`
- [x] Add an operational script or documented runtime path to push command
  definitions to Telegram (`scripts/register_telegram_commands.py`)

## Validation

- [x] Add tests for callback payload parsing and dispatch
  (`tests/test_menu.py::TestBuildCallback`, `TestParseCallback`, `TestIsMenuCallback`,
  `TestMenuCommandRouting`, `TestCallbackQueryRouting`)
- [x] Add tests for localized main-menu rendering (`tests/test_menu.py::TestRenderMainMenu`,
  `TestRenderLanguageScreen`, `TestRenderSettingsScreen`, `TestRenderBillingScreen`,
  `TestRenderHelpScreen`, `TestScreenRenderers`)
- [x] Add tests for language selection through the menu
  (`tests/test_menu.py::TestWebhookMenuCallback.test_language_set_*`)
- [x] Add tests for `ChatSettings` persistence (`tests/test_menu.py::TestChatSettings`)
- [x] Add tests for settings/billing stub screens and back navigation
  (`tests/test_menu.py::TestWebhookMenuCallback`)
- [x] Add tests for command routing of `/settings`, `/billing`, and `/help`
  (`tests/test_menu_routing.py::TestScreenCommandDispatch`, `TestWebhookScreenCommands`)
- [x] Add tests for localized Telegram command-definition payloads
  (`tests/test_command_registration.py`)
- [x] Run `python -m pytest -q` - 675 passed

## Follow-Up

- [ ] Decide the first real settings to expose in the menu after the foundation
- [ ] Decide the first payment provider and billing product model
- [ ] Decide whether to add a lightweight reply-keyboard launcher later
