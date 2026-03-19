# Feature Spec: Telegram Menu, Settings, and Billing Foundation

## Context

`flatscanner` now has a live Telegram MVP with multilingual output, but the
interaction model is still command- and free-text-first. That is fine for early
 testing, but it will not scale well once the bot needs discoverable language
 switching, user-configurable analysis settings, plan limits, and payment entry
 points.

The bot needs a minimal, polished menu system that feels intentional and easy to
 use on mobile without turning `router.py` into a large collection of one-off
 callback handlers. The right solution should also create clean extension points
 for future settings and billing flows.

## Scope

- Add a Telegram menu foundation based on inline keyboards and callback actions
- Add a `/menu` entry point and a primary menu screen
- Add a language screen reachable from the menu
- Add a generalized chat settings model instead of keeping language as a special
  one-off preference
- Add menu stubs for settings and billing so future iterations plug into stable
  navigation
- Keep the UX minimal, clean, and mobile-friendly

## Out Of Scope

- Full billing/payment provider integration
- Real entitlement enforcement or plan limits
- A large settings matrix in the first slice
- Reply-keyboard-first navigation as the primary UX
- Telegram Web App UI
- Non-Telegram channels

## Requirements

- The bot must expose a `/menu` command that opens a compact main menu
- The main menu must be driven by inline keyboards rather than forcing users to
  type commands for common actions
- The initial main menu must include clear entry points for language, settings,
  billing, and help
- The menu architecture must be screen-based so new menu screens can be added
  without scattering callback parsing logic across unrelated modules
- Callback payloads must use a stable, parseable schema rather than ad-hoc text
- Chat preferences must move toward a generalized `ChatSettings` model that can
  hold language and future bot settings
- Existing language switching must remain supported, but the menu path should
  become the primary UX for language selection
- The first menu slice must provide billing and settings screens as extensible
  placeholders even if those screens initially contain stub content
- Static menu labels and button text must flow through the existing i18n layer
- The UI should stay minimal: one primary menu message, concise copy, and no
  noisy persistent keyboard by default

## Acceptance Criteria

- Sending `/menu` returns a main menu with inline buttons for language,
  settings, billing, and help
- Selecting `Language` opens a language screen where the user can choose
  Russian, English, or Spanish
- Choosing a language updates the persisted chat settings and confirms the
  change in the selected language
- Selecting `Settings` opens a stub settings screen that is clearly structured
  for future expansion
- Selecting `Billing` opens a stub billing screen that can later host plan and
  payment actions
- Menu navigation supports back-to-main behavior without requiring free-text
  commands
- Tests cover callback parsing, menu rendering, language changes via the menu,
  and settings persistence behavior

## Decisions Made

- Primary Telegram UX will use inline keyboards plus callback-driven screens,
  with commands retained as fallbacks
- Reply keyboards may be added later as a lightweight launcher, but they are not
  the primary navigation layer in this feature
- Billing is introduced as a domain boundary and UI entry point before real
  payment provider wiring

## Open Questions

- Whether billing should first use Telegram-native payments or an external
  checkout link
- Which non-language settings should be exposed first after the foundation lands
