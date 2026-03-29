# Technical Plan: Bold Telegram Analysis Headings

## Approach

Use Telegram HTML parse mode only for the final analysis message.

## Planned Changes

1. Add a small HTML-safe formatting layer to `src/telegram/formatter.py`
2. Render headers and subheaders with `<b>...</b>`
3. Escape dynamic content before interpolation into the Telegram message
4. Extend `src/telegram/sender.py` so `send_message` can accept an optional
   `parse_mode`
5. Update `TelegramAnalysisPresenter` to send the final message with
   `parse_mode="HTML"`
6. Add focused formatter/sender tests

## Risks

- Unescaped dynamic content could break Telegram rendering
- Enabling parse mode too broadly could affect menus or progress UX

## Validation

- targeted formatter tests
- targeted sender/presenter path tests
