"""AI-backed review analysis service.

``ReviewAnalysisService`` sends a structured prompt built from ``ReviewsData``
to OpenRouter and parses the response into a ``ReviewAnalysisOutput``.

The service is intentionally focused: it only runs when there is at least one
review text to analyse.  Callers are responsible for checking
``ReviewsData.reviews`` before calling ``analyse``.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from src.analysis.openrouter_client import OpenRouterClient
from src.analysis.reviews.extractor import ReviewAnalysisOutput

if TYPE_CHECKING:
    from src.app.config import Settings
    from src.domain.review import ReviewsData

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a rental listing review analyst. "
    "Reply ONLY with a valid JSON object, no markdown, no text outside the JSON. "
    "Write all text fields in English. "
    "Use the schema from the user message."
)

_MAX_REVIEWS = 10
_MAX_REVIEW_CHARS = 300

_JSON_SCHEMA_HINT = """\
{
  "sentiment_summary": "<1-2 sentence summary of overall guest sentiment>",
  "common_themes": ["<positive theme 1>", "<positive theme 2>"],
  "concerns": ["<concern 1>", "<concern 2>"]
}"""


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def build_reviews_prompt(reviews_data: "ReviewsData") -> str:
    """Return a user-turn prompt for the given reviews data.

    Includes aggregate metadata and up to ``_MAX_REVIEWS`` review texts,
    each capped at ``_MAX_REVIEW_CHARS`` characters to control token cost.
    """
    lines: list[str] = ["Analyse these guest reviews for a rental listing.\n"]

    lines.append(f"Total reviews: {reviews_data.total_count}")
    if reviews_data.average_rating is not None:
        lines.append(f"Average rating: {reviews_data.average_rating:.2f} / 5")

    sample = [r for r in reviews_data.reviews if r.text][:_MAX_REVIEWS]
    if sample:
        lines.append("\nSample reviews:")
        for i, review in enumerate(sample, 1):
            text = review.text or ""
            if len(text) > _MAX_REVIEW_CHARS:
                text = text[:_MAX_REVIEW_CHARS] + "..."
            rating_suffix = f" [{review.rating:.1f}★]" if review.rating is not None else ""
            lines.append(f"  {i}. {text!r}{rating_suffix}")

    lines.append(
        f"\nReply ONLY with a JSON object matching this schema:\n{_JSON_SCHEMA_HINT}"
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def parse_reviews_response(raw: str) -> ReviewAnalysisOutput:
    """Parse the model's raw text response into a ``ReviewAnalysisOutput``.

    Lenient about code fences and whitespace; returns safe defaults for
    missing or invalid fields rather than raising.

    Parameters
    ----------
    raw:
        The text content returned by the model.

    Returns
    -------
    ReviewAnalysisOutput

    Raises
    ------
    ValueError
        If the text cannot be parsed as JSON or is not a JSON object.
    """
    text = raw.strip()

    # Strip ```json ... ``` fences if present
    if text.startswith("```"):
        lines_raw = text.splitlines()
        inner = lines_raw[1:] if lines_raw[0].startswith("```") else lines_raw
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        text = "\n".join(inner).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Review analysis response is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object from review analysis, got {type(data).__name__}"
        )

    sentiment_summary = data.get("sentiment_summary", "")
    if not isinstance(sentiment_summary, str):
        sentiment_summary = ""

    raw_themes = data.get("common_themes", [])
    common_themes = [str(t) for t in raw_themes if isinstance(t, str)] if isinstance(raw_themes, list) else []

    raw_concerns = data.get("concerns", [])
    concerns = [str(c) for c in raw_concerns if isinstance(c, str)] if isinstance(raw_concerns, list) else []

    return ReviewAnalysisOutput(
        sentiment_summary=sentiment_summary,
        common_themes=common_themes,
        concerns=concerns,
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ReviewAnalysisService:
    """Orchestrates AI analysis of extracted review data.

    Parameters
    ----------
    settings:
        Application settings; ``openrouter_api_key`` and
        ``openrouter_model`` are used to build the default client.
    client:
        Optional pre-built ``OpenRouterClient``.  When provided, *settings*
        is not used to construct the client (useful for testing).
    """

    def __init__(
        self,
        settings: "Settings",
        client: OpenRouterClient | None = None,
    ) -> None:
        self._client = client or OpenRouterClient(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
        )

    async def analyse(self, reviews_data: "ReviewsData") -> ReviewAnalysisOutput:
        """Run AI analysis on *reviews_data* and return structured output.

        Parameters
        ----------
        reviews_data:
            Extracted reviews with aggregate metadata.  At least one review
            with a non-empty ``text`` should be present for a meaningful
            analysis; the caller is responsible for this check.

        Returns
        -------
        ReviewAnalysisOutput

        Raises
        ------
        OpenRouterError
            If the OpenRouter API call fails.
        ValueError
            If the model's response cannot be parsed as a valid
            ``ReviewAnalysisOutput``.
        """
        prompt = build_reviews_prompt(reviews_data)
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        logger.debug(
            "Sending review analysis request (%d reviews) to OpenRouter",
            len(reviews_data.reviews),
        )
        raw = await self._client.chat(messages)

        try:
            result = parse_reviews_response(raw)
        except ValueError:
            logger.error(
                "Failed to parse OpenRouter review analysis response: %r", raw[:200]
            )
            raise

        return result
