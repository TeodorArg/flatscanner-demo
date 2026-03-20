# Feature Spec: Review Insights In User Output

## Context

`019-review-analysis-module` and `023-review-analysis-skill-and-unified-corpus`
already compute provider-aware review insights:

- incident-oriented overall assessment
- recurring issues
- critical red flags
- conflicts/disputes
- positive signals
- window-view summary

Those results currently stop at the module layer. The Telegram user still sees
only the AI summary / strengths / risks / price block, so the new review module
is invisible in the final product.

## Scope

- Add a dedicated reviews block to the final user-facing analysis message.
- Keep the block compact and deterministic so the Telegram output stays readable.
- Thread `ReviewsResult` through the processing/rendering path without breaking
  the existing canonical-English + on-demand translation architecture.
- Localize block labels through the existing i18n catalog.
- Translate the new freeform review block content through the existing
  translation stage for non-English output.

## Out Of Scope

- Result cache.
- Billing / entitlements.
- Additional specialist modules beyond reviews.
- A full generic result-assembly layer for all future modules.

## User-Facing Behavior

When review insights are available, the final Telegram output includes a
separate reviews section after the summary/strengths/risks block and before the
price line.

The section should prefer concise, high-signal content:

- compact review overview
- critical red flags when present
- recurring issues when present
- conflicts/disputes when present
- window-view summary when present

If only review metadata exists (count/rating without AI insights), the section
may render a minimal overview or be omitted; the implementation should favor a
short, useful result over placeholder noise.

## Contracts

Introduce a compact nested result block carried with `AnalysisResult`, for
example:

```python
class ReviewInsightsBlock(BaseModel):
    overall_assessment: str = ""
    overall_risk_level: str = ""
    review_count: int | None = None
    average_rating: float | None = None
    critical_red_flags: list[str] = []
    recurring_issues: list[str] = []
    conflicts_or_disputes: list[str] = []
    positive_signals: list[str] = []
    window_view_summary: str = ""
```

The exact shape may vary slightly in implementation, but it must stay compact,
translation-friendly, and formatter-friendly.

## Acceptance Criteria

- `process_job` consumes `ReviewsResult` and maps it into the final renderable
  analysis result.
- Non-English jobs translate the new review block together with the existing
  freeform result fields.
- The formatter renders a dedicated localized reviews section when useful review
  insights exist.
- Formatter output remains bounded and deterministic.
- Focused tests cover:
  - processor mapping from `ReviewsResult`
  - translation of review block fields
  - formatter rendering / omission behavior
  - multilingual labels for the reviews section
