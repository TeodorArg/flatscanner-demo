"""Analysis result schema.

This module defines the structured output of the AI analysis step.
The ``AnalysisResult`` model is intentionally narrow for the first MVP
slice: summary, strengths, risks, and a price-fairness verdict with a
short explanation.
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


class AnalysisResult(BaseModel):
    """Structured output from the AI analysis stage.

    Produced by ``AnalysisService.analyse`` and intended for downstream
    Telegram formatting.  All text fields come from the model response;
    ``price_verdict`` is constrained to a known enum set so callers can
    branch on it without string-matching.
    """

    summary: str = Field(description="1–2 sentence overview of the listing.")
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
