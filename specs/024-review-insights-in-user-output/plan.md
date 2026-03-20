# Implementation Plan: 024-review-insights-in-user-output

## New files

| File | Purpose |
|---|---|
| `tests/test_review_output_block.py` | focused rendering / mapping / translation tests |

## Changed files

| File | Change |
|---|---|
| `src/analysis/result.py` | add compact review insights block carried with `AnalysisResult` |
| `src/jobs/processor.py` | map `ReviewsResult` into the final renderable result |
| `src/translation/service.py` | translate review-block freeform fields for non-English output |
| `src/telegram/formatter.py` | render a localized review section |
| `src/i18n/catalog.py` | add localized labels for the reviews section |
| `tests/test_job_processor.py` | integration coverage for review-output mapping |
| `tests/test_telegram_formatter.py` | formatter coverage for review section |
| `tests/test_translation_service.py` | translation coverage for review block |
| `specs/024-review-insights-in-user-output/tasks.md` | task tracking |

## Approach

Keep this slice small and additive:

1. Add a compact nested review block to the renderable result schema.
2. Flatten `ReviewsResult` into a concise user-facing shape inside `process_job`.
3. Extend the translation prompt/parser to include the new review freeform
   fields while preserving the canonical-English architecture.
4. Render the block with localized labels and omission rules that avoid noisy
   empty sections.
5. Keep the rest of the module framework unchanged.
