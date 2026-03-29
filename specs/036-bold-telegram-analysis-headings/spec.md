# Feature Spec: Bold Telegram Analysis Headings

## Goal

Improve readability of the final Telegram analysis message by making section
headers and subheaders visually distinct with bold styling.

## Problem

The current Telegram formatter emits plain text only. As more structured blocks
were added, the final message became harder to scan because headers, subheaders,
and block labels blend into body text and bullets.

## Scope

In scope:

- bold formatting for the final Telegram analysis output
- section headers and subheaders only
- safe Telegram rendering without enabling formatting globally for menus or
  progress messages

Out of scope:

- wording changes for the analysis content itself
- menu/progress message formatting
- non-Telegram channels

## Acceptance Criteria

- final analysis messages render section headers in bold in Telegram
- nested subheaders inside reviews and pricing blocks also render in bold
- dynamic user-facing text remains safely escaped
- plain menu and progress messages remain unaffected
