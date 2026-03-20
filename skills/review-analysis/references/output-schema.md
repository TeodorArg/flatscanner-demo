# Review Analysis Output Schema

Return strict JSON with this shape:

```json
{
  "overall_assessment": "short overall summary",
  "overall_risk_level": "low|medium|high",
  "confidence": "low|medium|high",
  "incident_timeline": [
    {
      "category": "mold_damp_smell",
      "severity": "low|medium|high",
      "incident_date": "2026-02-28",
      "source_comment_index": 3,
      "summary": "Guest reported mold smell near the bedroom.",
      "evidence": "There was a damp mold smell near the bed."
    }
  ],
  "recurring_issues": [
    {
      "category": "temperature",
      "count": 4,
      "summary": "Several guests reported the apartment was too cold."
    }
  ],
  "conflicts_or_disputes": [
    {
      "incident_date": "2026-01-10",
      "summary": "Guest described a refund dispute with the host."
    }
  ],
  "critical_red_flags": ["Cockroach mention in multiple reviews"],
  "positive_signals": ["Great natural light", "Pleasant window view"],
  "window_view_summary": "Mixed evidence: some guests praised the city view, one said it faced a noisy courtyard."
}
```

Rules:

- Use empty lists, not nulls.
- Use explicit confidence.
- Do not invent dates or incidents not grounded in comments.
- When evidence is mixed, say so.
