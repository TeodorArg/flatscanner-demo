"""Analysis result schema.

This module defines the structured output of the AI analysis step.
The ``AnalysisResult`` model stays intentionally compact for the MVP:
summary, strengths, risks, a price-fairness verdict, and an optional
localized display title used by the final Telegram renderer.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class PriceVerdict(str, Enum):
    """High-level price-fairness assessment."""

    FAIR = "fair"
    OVERPRICED = "overpriced"
    UNDERPRICED = "underpriced"
    UNKNOWN = "unknown"


class ReviewInsightsBlock(BaseModel):
    """Compact review insights carried with ``AnalysisResult`` for rendering.

    Populated by the job processor from ``ReviewsResult``.  All freeform text
    fields are in canonical English and translated together with the rest of
    the analysis result before the formatter receives them.
    """

    overall_assessment: str = ""
    overall_risk_level: str = ""
    review_count: int | None = None
    average_rating: float | None = None
    critical_red_flags: list[str] = Field(default_factory=list)
    recurring_issues: list[str] = Field(default_factory=list)
    conflicts_or_disputes: list[str] = Field(default_factory=list)
    positive_signals: list[str] = Field(default_factory=list)
    window_view_summary: str = ""


class AnalysisResult(BaseModel):
    """Structured output from the AI analysis stage.

    Produced by ``AnalysisService.analyse`` and intended for downstream
    Telegram formatting. ``price_verdict`` is constrained to a known enum
    set so callers can branch on it without string-matching.

    ``display_title`` is an optional user-facing header derived from the
    provider listing title. It is attached by the processing/rendering
    pipeline so the final message can localize the header together with
    the translated analysis blocks.
    """

    display_title: str = Field(
        default="",
        description="Localized title/header shown above the analysis summary.",
    )
    summary: str = Field(description="1-2 sentence overview of the listing.")
    strengths: list[str] = Field(
        default_factory=list,
        description="Notable positive aspects of the listing.",
    )
    risks: list[str] = Field(
        default_factory=list,
        description="Potential concerns or drawbacks.",
    )
    price_verdict: PriceVerdict = Field(
        default=PriceVerdict.UNKNOWN,
        description="High-level price-fairness verdict.",
    )
    price_explanation: str = Field(
        default="",
        description="One sentence explaining the price assessment.",
    )
    review_insights: ReviewInsightsBlock | None = Field(
        default=None,
        description="Compact review insights block; None when no review data is available.",
    )
