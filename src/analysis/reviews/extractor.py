"""Review extractor contract and AI analysis output model.

``ReviewExtractor`` is the structural protocol satisfied by the legacy
extractor classes (``AirbnbReviewExtractor``, ``GenericReviewExtractor``).
New code should prefer the normalizer classes in
``src.analysis.reviews.normalizers`` which produce the unified corpus.

``ReviewAnalysisOutput`` is the structured result returned by
``ReviewAnalysisService`` using the incident-oriented output schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from src.domain.listing import NormalizedListing
    from src.domain.review import ReviewsData


# ---------------------------------------------------------------------------
# Legacy extractor protocol (kept for backward compatibility)
# ---------------------------------------------------------------------------


class ReviewExtractor(Protocol):
    """Protocol satisfied by every legacy review extractor implementation.

    An extractor maps a raw provider payload and a normalized listing into
    a ``ReviewsData`` object.  Implementations must be pure (no I/O).

    .. deprecated::
        New work should use provider normalizers in
        ``src.analysis.reviews.normalizers`` that output ``ReviewCorpus``.
    """

    def extract(
        self,
        payload: dict[str, Any],
        listing: "NormalizedListing",
    ) -> "ReviewsData": ...


# ---------------------------------------------------------------------------
# AI analysis output — incident-oriented schema
# ---------------------------------------------------------------------------


@dataclass
class ReviewAnalysisOutput:
    """Structured output produced by ``ReviewAnalysisService``.

    All fields have safe defaults so partial model responses are handled
    gracefully.  List fields use empty lists rather than ``None`` per the
    output schema contract.
    """

    overall_assessment: str = ""
    overall_risk_level: str = ""
    confidence: str = ""
    incident_timeline: list[dict] = field(default_factory=list)
    recurring_issues: list[dict] = field(default_factory=list)
    conflicts_or_disputes: list[dict] = field(default_factory=list)
    critical_red_flags: list[str] = field(default_factory=list)
    positive_signals: list[str] = field(default_factory=list)
    window_view_summary: str = ""
