"""Reviews analysis modules.

Provides two implementations of the reviews analysis module:

``AirbnbReviewsModule``
    Provider-specific module for Airbnb listings.  Fetches reviews from the
    dedicated ``tri_angle~airbnb-reviews-scraper`` actor via
    ``AirbnbReviewSource`` when configured, normalizes them with
    ``AirbnbReviewNormalizer.normalize_from_actor_items()``, then runs an AI
    analysis with ``ReviewAnalysisService`` when at least one comment text is
    present.

    Fallback chain (most specific first):
    1. Dedicated reviews actor (``review_source`` is set and fetch succeeds)
    2. Listing raw payload (``ctx.raw_payload`` is present and has reviews)
    3. Generic metadata-only (listing ``review_count`` / ``rating`` fields)

    The module degrades gracefully at each level: a failed actor fetch falls
    back to the listing payload; a failed AI call returns metadata-only.

``GenericReviewsModule``
    Generic fallback module for any provider.  Uses ``GenericReviewNormalizer``
    to build a ``ReviewCorpus`` from listing-level metadata and returns a
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
from src.analysis.reviews.normalizers.airbnb import AirbnbReviewNormalizer
from src.analysis.reviews.normalizers.generic import GenericReviewNormalizer
from src.domain.listing import ListingProvider

if TYPE_CHECKING:
    from src.analysis.context import AnalysisContext
    from src.analysis.reviews.airbnb_source import AirbnbReviewSource
    from src.analysis.reviews.service import ReviewAnalysisService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class ReviewsResult(ModuleResult):
    """Output from the reviews analysis module.

    ``review_count`` and ``average_rating`` are always sourced from the
    normalized corpus.  The incident-oriented AI fields are populated only
    when comment texts were available and ``ReviewAnalysisService`` succeeded.
    """

    review_count: int | None = None
    average_rating: float | None = None
    overall_assessment: str | None = None
    overall_risk_level: str | None = None
    confidence: str | None = None
    incident_timeline: list[dict] = field(default_factory=list)
    recurring_issues: list[dict] = field(default_factory=list)
    conflicts_or_disputes: list[dict] = field(default_factory=list)
    critical_red_flags: list[str] = field(default_factory=list)
    positive_signals: list[str] = field(default_factory=list)
    window_view_summary: str | None = None


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
    review_source:
        Optional ``AirbnbReviewSource`` for fetching reviews from the
        dedicated ``tri_angle~airbnb-reviews-scraper`` actor.  When provided,
        the module fetches reviews directly rather than relying on the listing
        raw payload.  Falls back to the listing payload when ``None`` or when
        the fetch raises an exception.
    """

    name = "reviews"
    supported_providers: frozenset[ListingProvider] = frozenset({ListingProvider.AIRBNB})

    def __init__(
        self,
        service: "ReviewAnalysisService",
        review_source: "AirbnbReviewSource | None" = None,
    ) -> None:
        self._service = service
        self._review_source = review_source
        self._airbnb_normalizer = AirbnbReviewNormalizer()
        self._generic_normalizer = GenericReviewNormalizer()

    async def run(self, ctx: "AnalysisContext") -> ReviewsResult:
        """Normalize reviews and optionally run AI analysis.

        Fetch order:
        1. Dedicated reviews actor (when ``review_source`` is set and listing
           URL is available).  A failed fetch is logged and silently skipped.
        2. Listing raw payload (``ctx.raw_payload``).
        3. Generic normalizer (metadata-only fallback).

        Parameters
        ----------
        ctx:
            Analysis context.  ``ctx.listing.source_url`` is passed to the
            reviews actor; ``ctx.raw_payload`` is used as fallback.

        Returns
        -------
        ReviewsResult
            Populated with AI analysis fields when comment texts are available,
            metadata-only otherwise.
        """
        extraction = None

        # 1. Dedicated reviews actor
        if self._review_source is not None and ctx.listing.source_url:
            try:
                items = await self._review_source.fetch(ctx.listing.source_url)
                extraction = self._airbnb_normalizer.normalize_from_actor_items(
                    items, ctx.listing
                )
            except Exception:
                logger.warning(
                    "Airbnb reviews actor fetch failed; falling back to listing payload",
                    exc_info=True,
                )

        # 2. Listing raw payload fallback
        if extraction is None:
            if ctx.raw_payload is not None:
                extraction = self._airbnb_normalizer.normalize(
                    ctx.raw_payload.payload, ctx.listing
                )
            else:
                extraction = self._generic_normalizer.normalize({}, ctx.listing)

        corpus = extraction.corpus

        # Run AI analysis only when there is something to analyse.
        has_text = any(c.comment_text for c in corpus.comments)
        if has_text:
            try:
                output = await self._service.analyse(corpus)
                return ReviewsResult(
                    module_name=self.name,
                    review_count=corpus.total_review_count,
                    average_rating=corpus.average_rating,
                    overall_assessment=output.overall_assessment or None,
                    overall_risk_level=output.overall_risk_level or None,
                    confidence=output.confidence or None,
                    incident_timeline=output.incident_timeline,
                    recurring_issues=output.recurring_issues,
                    conflicts_or_disputes=output.conflicts_or_disputes,
                    critical_red_flags=output.critical_red_flags,
                    positive_signals=output.positive_signals,
                    window_view_summary=output.window_view_summary or None,
                )
            except Exception:
                logger.warning(
                    "Review AI analysis failed; degrading to metadata-only result",
                    exc_info=True,
                )

        return ReviewsResult(
            module_name=self.name,
            review_count=corpus.total_review_count,
            average_rating=corpus.average_rating,
        )


# ---------------------------------------------------------------------------
# Generic fallback module
# ---------------------------------------------------------------------------


class GenericReviewsModule:
    """Generic reviews module for any listing provider.

    Uses listing-level metadata only; no AI call is made.  This module
    acts as the fallback when no provider-specific reviews module is
    registered or when the provider is unknown.
    """

    name = "reviews"
    supported_providers: frozenset[ListingProvider] = frozenset()  # generic

    def __init__(self) -> None:
        self._normalizer = GenericReviewNormalizer()

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
        extraction = self._normalizer.normalize({}, ctx.listing)
        corpus = extraction.corpus
        return ReviewsResult(
            module_name=self.name,
            review_count=corpus.total_review_count,
            average_rating=corpus.average_rating,
        )
