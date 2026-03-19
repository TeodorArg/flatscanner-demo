# Feature Spec: Multilingual Bot Output

## Context

`flatscanner` already supports the first live Telegram MVP flow, but the user-facing result is currently single-language. The bot now needs multilingual output for Russian, English, and Spanish, with Russian as the default user language.

The project should avoid multiplying prompt sets and analysis logic per language. The chosen direction is:

- keep the canonical AI analysis result in English
- localize bot interface strings through an application i18n layer
- translate only the freeform AI-generated result blocks into the user's selected language before formatting the final Telegram reply

This keeps the analysis pipeline unified while still allowing user-facing localization.

## Scope

- Add user-selectable output languages: `ru`, `en`, `es`
- Default new Telegram chats to Russian
- Add a language preference per Telegram chat
- Snapshot the selected language onto each queued analysis job
- Introduce an i18n layer for bot/system strings
- Keep canonical structured analysis results in English
- Add a translation stage for AI-generated freeform result blocks
- Add translation caching keyed by analysis result and target language
- Format the final Telegram reply in the selected language

## Out Of Scope

- Automatic language detection from Telegram locale or message text
- Translating provider payloads or normalized listing fields at ingest time
- Rewriting all analysis prompts into three full language variants
- Adding more languages beyond Russian, English, and Spanish
- Translating raw source data or enrichment payloads for storage

## Requirements

- The bot must support `ru`, `en`, and `es` as explicit user-facing output languages
- The default language for a new Telegram chat must be Russian
- The selected language must apply to all user-facing text sent by the bot
- A chat's language preference must be persisted and reused for future requests
- Each analysis job must capture the effective language at enqueue time so in-flight jobs remain stable even if the chat preference changes later
- Canonical AI analysis storage must remain in English for freeform generated blocks
- Structured non-freeform fields such as `price_verdict` must remain language-neutral
- Bot UI/system strings must come from a centralized i18n catalog rather than language-specific branching scattered through the codebase
- Translation must happen on structured freeform blocks before formatting, not inside the final formatter itself
- Translation results must be cacheable per analysis result and target language
- When a translation cache entry exists for a given analysis result and target language, the bot must reuse it instead of issuing a new translation call
- Final Telegram formatting must use the selected language's labels and wording

## Acceptance Criteria

- A new Telegram chat with no saved preference receives Russian bot UI text by default
- A user can switch the bot language between Russian, English, and Spanish
- The bot persists the chosen language and uses it for subsequent requests from the same chat
- An analysis job queued while the chat language is Russian still returns Russian output even if the user changes the chat preference before the job finishes
- The canonical stored analysis result remains English for freeform blocks
- A Russian or Spanish response is produced by translating the canonical English freeform blocks and combining them with localized formatter labels
- Repeated requests for the same analysis result in the same target language reuse cached translation data
- Tests cover language preference persistence, job-language snapshotting, translation-stage behavior, formatter localization, and fallback behavior

## Open Questions

- Whether translation should use the same primary analysis model or a cheaper dedicated translation model
- Whether translated results should be persisted in PostgreSQL, Redis, or both
- Whether language switching UX should be command-based, button-based, or hybrid
