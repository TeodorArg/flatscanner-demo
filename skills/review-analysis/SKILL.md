---
name: review-analysis
description: Extract, normalize, and analyze guest review comments for rental listings. Use when implementing or extending review normalizers, review prompts, incident extraction, risk summarization, or provider-specific review handling for Airbnb, Booking, or generic fallback.
---

# Review Analysis

Normalize provider-specific review payloads into a single review corpus before any AI analysis.

Use this skill to keep review analysis evidence-first and incident-oriented.

## Workflow

1. Normalize raw provider reviews into one `ReviewCorpus`.
2. Preserve comment text, dates, ratings, language, host response, and provider ids when available.
3. Analyze comments for concrete incidents, not sentiment alone.
4. Prioritize negative signals, disputes, unusual situations, and repeated complaints.
5. Return structured JSON only.

## Priority Categories

Read [references/categories.md](references/categories.md) before changing the taxonomy.

Always pay special attention to:
- pests
- damage
- missing essentials
- mold, dampness, smells
- temperature problems
- cleanliness
- safety
- host conflict
- listing mismatch
- noise
- check-in and access
- window view

## Output Contract

Read [references/output-schema.md](references/output-schema.md) before changing prompt or parsing logic.

Rules:
- attach supporting evidence to serious claims
- include incident dates when comments provide them
- mark mixed or weak evidence conservatively
- prefer `confidence=low` over overclaiming
