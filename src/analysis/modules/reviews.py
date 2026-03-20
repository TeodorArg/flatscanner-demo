"""Reviews analysis modules.

Provides two implementations of the reviews analysis module:

``AirbnbReviewsModule``
    Provider-specific module for Airbnb listings.  Extracts reviews from the
    raw payload via ``AirbnbReviewExtractor``, then runs an AI analysis with
    ``ReviewAnalysisService`` when at least one review text is present.
    Falls back to ``GenericReviewExtractor`` when ``ctx.raw_payload`` is
    ``None`` (e.g. raw payload capture was disabled or failed).

``GenericReviewsModule``
    Generic fallback module for any provider.  Uses ``GenericReviewExtractor``
    to build ``ReviewsData`` from listing-level metadata and returns a
    ``ReviewsResult`` with count and rating only — no AI call.

Both modules share the name ``"reviews"``.  The registry resolves
``AirbnbReviewsModule`` for Airbnb listings and ``GenericReviewsModule`` for
all other providers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.analysis.module import ModuleResult
from src.analysis.reviews.airbnb_extractor import AirbnbReviewExtractor
from src.analysis.reviews.generic_extractor import GenericReviewExtractor
from src.domain.listing import ListingProvider

if TYPE_CHECKING:
    from src.analysis.context import AnalysisContext
    from src.analysis.reviews.service import ReviewAnalysisService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class ReviewsResult(ModuleResult):
    """Output from the reviews analysis module.

    ``review_count`` and ``average_rating`` are sourced from the extracted
    ``ReviewsData``.  The AI-generated fields are populated only when review
    texts were available and the ``ReviewAnalysisService`` was invoked.
    """

    review_count: int | None = None
    average_rating: float | None = None
    sentiment_summary: str | None = None
    common_themes: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Airbnb-specific module
# ---------------------------------------------------------------------------


class AirbnbReviewsModule:
    """Provider-specific reviews module for Airbnb listings.

    Parameters
    ----------
    service:
        Pre-built ``ReviewAnalysisService`` used for AI-backed analysis.
        Callers are responsible for constructing and configuring it.
    """

    name = "reviews"
    supported_providers: frozenset[ListingProvider] = frozenset({ListingProvider.AIRBNB})

    def __init__(self, service: "ReviewAnalysisService") -> None:
        self._service = service
        self._airbnb_extractor = AirbnbReviewExtractor()
        self._generic_extractor = GenericReviewExtractor()

    async def run(self, ctx: "AnalysisContext") -> ReviewsResult:
        """Extract reviews from the raw payload and optionally run AI analysis.

        Parameters
        ----------
        ctx:
            Analysis context.  ``ctx.raw_payload`` is used when present;
            falls back to ``GenericReviewExtractor`` otherwise.

        Returns
        -------
        ReviewsResult
            Populated with AI analysis fields when review texts are available,
            metadata-only otherwise.
        """
        if ctx.raw_payload is not None:
            reviews_data = self._airbnb_extractor.extract(
                ctx.raw_payload.payload, ctx.listing
            )
        else:
            reviews_data = self._generic_extractor.extract({}, ctx.listing)

        # Run AI analysis only when there is something to analyse.
        has_text = any(r.text for r in reviews_data.reviews)
        if has_text:
            try:
                output = await self._service.analyse(reviews_data)
                return ReviewsResult(
                    module_name=self.name,
                    review_count=reviews_data.total_count or None,
                    average_rating=reviews_data.average_rating,
                    sentiment_summary=output.sentiment_summary or None,
                    common_themes=output.common_themes,
                    concerns=output.concerns,
                )
            except Exception:
                logger.warning(
                    "Review AI analysis failed; degrading to metadata-only result",
                    exc_info=True,
                )

        return ReviewsResult(
            module_name=self.name,
            review_count=reviews_data.total_count or None,
            average_rating=reviews_data.average_rating,
        )


# ---------------------------------------------------------------------------
# Generic fallback module
# ---------------------------------------------------------------------------


class GenericReviewsModule:
    """Generic reviews module for any listing provider.

    Uses listing-level metadata only; no AI call is made.  This module
    acts as the fallback when no provider-specific reviews module is
    registered or when provider is unknown.
    """

    name = "reviews"
    supported_providers: frozenset[ListingProvider] = frozenset()  # generic

    def __init__(self) -> None:
        self._extractor = GenericReviewExtractor()

    async def run(self, ctx: "AnalysisContext") -> ReviewsResult:
        """Return a metadata-only ``ReviewsResult`` from listing fields.

        Parameters
        ----------
        ctx:
            Analysis context providing listing metadata.

        Returns
        -------
        ReviewsResult
            ``review_count`` and ``average_rating`` sourced from the listing.
            AI fields are always ``None`` / empty.
        """
        reviews_data = self._extractor.extract({}, ctx.listing)
        return ReviewsResult(
            module_name=self.name,
            review_count=reviews_data.total_count or None,
            average_rating=reviews_data.average_rating,
        )
