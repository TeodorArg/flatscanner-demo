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

- [ ] Add Telegram menu callback parsing and screen rendering foundation
- [ ] Add `/menu` command handling
- [ ] Add main menu inline keyboard and localized copy
- [ ] Introduce generalized `ChatSettings` storage and migrate language access
- [ ] Add menu-based language selection screen
- [ ] Keep `/language` fallback behavior working on top of the settings layer
- [ ] Add stub settings screen designed for future options
- [ ] Add stub billing screen designed for future plans and checkout flows
- [ ] Add i18n strings for menu labels, buttons, and navigation feedback

## Validation

- [ ] Add tests for callback payload parsing and dispatch
- [ ] Add tests for localized main-menu rendering
- [ ] Add tests for language selection through the menu
- [ ] Add tests for `ChatSettings` persistence
- [ ] Add tests for settings/billing stub screens and back navigation
- [ ] Run `python -m pytest -q`

## Follow-Up

- [ ] Decide the first real settings to expose in the menu after the foundation
- [ ] Decide the first payment provider and billing product model
- [ ] Decide whether to add a lightweight reply-keyboard launcher later
