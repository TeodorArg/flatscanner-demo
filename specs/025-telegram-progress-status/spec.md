# Spec 025 — Telegram Analysis Progress UX

## Problem

When a user sends an Airbnb URL the bot immediately replies with an "analysing…" message that echoes the URL and gives no indication of how long to wait. The worker may take 1–2 minutes to complete; in that time the user sees a stale message with no further updates.

## Goal

Replace the immediate reply with a localized progress message that:

1. Does **not** echo the submitted URL.
2. Sets expectations by saying analysis can take around 2 minutes.
3. Shows coarse-grained stage updates while the worker processes the job.
4. Provides a Telegram typing indicator heartbeat during processing.
5. Deletes the progress message before the final result is delivered, so the chat contains only the result.

## Behaviour

### Router (webhook handler)

- On `analyse` decision: send the progress message via `sendMessage`, record the returned `message_id` on the `AnalysisJob` as `telegram_progress_message_id`, then enqueue the job.
- If the send fails, propagate the error as before (no silent swallow at the router level).
- The progress message text is the `msg.analysing` catalog string (no URL placeholder).

### Worker / Processor

- On job start: begin a background typing-action heartbeat (fires `sendChatAction` with `typing` every 4 s until cancelled).
- After adapter resolved / before fetch: update progress message to `msg.progress.fetching`.
- After listing fetched / before analysis: update progress message to `msg.progress.analysing`.
- Before final `sendMessage`: delete the progress message via `deleteMessage`.
- **All progress operations are best-effort**: any failure is logged at DEBUG and swallowed. They must never abort the pipeline or affect the final result.

### i18n

New catalog keys:

| Key | RU | EN | ES |
|---|---|---|---|
| `msg.analysing` | Анализирую объявление — это займёт около 2 минут… | Analysing your listing — this can take around 2 minutes… | Analizando tu anuncio — esto puede tardar unos 2 minutos… |
| `msg.progress.fetching` | Загружаю данные объявления… | Fetching listing details… | Obteniendo detalles del anuncio… |
| `msg.progress.analysing` | Запускаю ИИ-анализ… | Running AI analysis… | Ejecutando análisis de IA… |

## Non-goals

- No persistent storage of progress state.
- No per-stage time estimates.
- No progress bar / percentage.
- No retry logic for progress update failures.
