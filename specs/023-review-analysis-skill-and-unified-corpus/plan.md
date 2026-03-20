# Implementation Plan: 023-review-analysis-skill-and-unified-corpus

## New files

| File | Purpose |
|---|---|
| `skills/review-analysis/SKILL.md` | concise reusable workflow for review analysis |
| `skills/review-analysis/references/categories.md` | incident taxonomy, including window view |
| `skills/review-analysis/references/output-schema.md` | strict JSON result contract |
| `src/domain/review_corpus.py` | unified review corpus models |
| `src/analysis/reviews/normalizers/airbnb.py` | Airbnb -> unified corpus |
| `src/analysis/reviews/normalizers/generic.py` | generic fallback -> unified corpus |
| `tests/test_review_corpus_normalization.py` | normalization tests |

## Changed files

| File | Change |
|---|---|
| `src/analysis/reviews/service.py` | consume the unified corpus and stricter incident-oriented schema |
| `src/analysis/modules/reviews.py` | use normalizers instead of provider-shaped extractors |
| `src/jobs/processor.py` | keep current live wiring while adopting the new corpus models |
| `docs/project/backend/backend-docs.md` | record the repository skill approach for analysis modules |
| `specs/023-review-analysis-skill-and-unified-corpus/tasks.md` | task tracking |

## Approach

Do this in small steps:

1. Add the repository skill and references.
2. Introduce the unified review corpus models.
3. Migrate Airbnb and generic extraction into provider normalizers.
4. Tighten the review analysis prompt/output around incidents, red flags, disputes, dates, and view-from-window signals.
5. Keep current Telegram output unchanged until a later report-assembly task.
