"""Review extractor contract and AI analysis output model.

``ReviewExtractor`` is the structural protocol that all review extractors
must satisfy.  ``ReviewAnalysisOutput`` is the structured result returned
by ``ReviewAnalysisService``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from src.domain.listing import NormalizedListing
    from src.domain.review import ReviewsData


# ---------------------------------------------------------------------------
# Extractor protocol
# ---------------------------------------------------------------------------


class ReviewExtractor(Protocol):
    """Protocol satisfied by every review extractor implementation.

    An extractor maps a raw provider payload and a normalized listing into
    a ``ReviewsData`` object.  Implementations must be pure (no I/O).
    """

    def extract(
        self,
        payload: dict[str, Any],
        listing: "NormalizedListing",
    ) -> "ReviewsData": ...


# ---------------------------------------------------------------------------
# AI analysis output
# ---------------------------------------------------------------------------


@dataclass
class ReviewAnalysisOutput:
    """Structured output produced by ``ReviewAnalysisService``.

    All fields have safe defaults so partial model responses are handled
    gracefully.
    """

    sentiment_summary: str = ""
    common_themes: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
