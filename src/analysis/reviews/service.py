"""AI-backed review analysis service.

``ReviewAnalysisService`` sends a structured prompt built from a
``ReviewCorpus`` to OpenRouter and parses the response into a
``ReviewAnalysisOutput`` using the incident-oriented output schema.

The service is intentionally focused: it only runs when there is at least one
comment text to analyse.  Callers are responsible for checking
``ReviewCorpus.comments`` before calling ``analyse``.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from src.analysis.openrouter_client import OpenRouterClient
from src.analysis.reviews.extractor import ReviewAnalysisOutput

if TYPE_CHECKING:
    from src.app.config import Settings
    from src.domain.review_corpus import ReviewCorpus

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a rental listing review analyst. "
    "Reply ONLY with a valid JSON object, no markdown, no text outside the JSON. "
    "Write all text fields in English. "
    "Use the schema from the user message. "
    "Focus on concrete incidents, not generic sentiment. "
    "Emphasize negative signals, disputes, and unusual situations. "
    "Do not invent dates or incidents not grounded in the comments."
)

_MAX_REVIEWS = 20
_MAX_REVIEW_CHARS = 400
_MAX_HOST_RESPONSE_CHARS = 200

_JSON_SCHEMA_HINT = """\
{
  "overall_assessment": "<1-2 sentence summary>",
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
  "window_view_summary": "Mixed: some guests praised the city view, one said it faced a noisy courtyard."
}

Categories: pests, damage, missing_essentials, mold_damp_smell, temperature, cleanliness, \
safety, host_conflict, listing_mismatch, noise, checkin_access, window_view.
Use empty lists, not nulls. Always include window_view_summary (empty string if no evidence)."""


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def build_reviews_prompt(corpus: "ReviewCorpus") -> str:
    """Return a user-turn prompt for the given review corpus.

    Includes aggregate metadata and up to ``_MAX_REVIEWS`` comment texts,
    each capped at ``_MAX_REVIEW_CHARS`` characters to control token cost.
    Comments are numbered so the model can reference them via
    ``source_comment_index`` in the output.
    """
    lines: list[str] = ["Analyse these guest reviews for a rental listing.\n"]

    if corpus.total_review_count is not None:
        lines.append(f"Total reviews: {corpus.total_review_count}")
    if corpus.average_rating is not None:
        lines.append(f"Average rating: {corpus.average_rating:.2f} / 5")

    sample = [c for c in corpus.comments if c.comment_text][:_MAX_REVIEWS]
    if sample:
        lines.append("\nSample reviews (numbered for reference):")
        for i, comment in enumerate(sample, 1):
            parts: list[str] = [f"  {i}."]
            if comment.review_date:
                parts.append(f"[{comment.review_date}]")
            if comment.rating is not None:
                parts.append(f"[{comment.rating:.1f}★]")
            text = comment.comment_text
            if len(text) > _MAX_REVIEW_CHARS:
                text = text[:_MAX_REVIEW_CHARS] + "..."
            parts.append(repr(text))
            lines.append(" ".join(parts))
            if comment.host_response_text:
                host_text = comment.host_response_text
                if len(host_text) > _MAX_HOST_RESPONSE_CHARS:
                    host_text = host_text[:_MAX_HOST_RESPONSE_CHARS] + "..."
                lines.append(f"     Host response: {host_text!r}")

    lines.append(
        f"\nReply ONLY with a JSON object matching this schema:\n{_JSON_SCHEMA_HINT}"
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def _parse_list_of_dicts(data: object) -> list[dict]:
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _parse_list_of_str(data: object) -> list[str]:
    if not isinstance(data, list):
        return []
    return [str(item) for item in data if isinstance(item, str)]


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

    overall_assessment = data.get("overall_assessment", "")
    if not isinstance(overall_assessment, str):
        overall_assessment = ""

    overall_risk_level = data.get("overall_risk_level", "")
    if not isinstance(overall_risk_level, str):
        overall_risk_level = ""

    confidence = data.get("confidence", "")
    if not isinstance(confidence, str):
        confidence = ""

    window_view_summary = data.get("window_view_summary", "")
    if not isinstance(window_view_summary, str):
        window_view_summary = ""

    return ReviewAnalysisOutput(
        overall_assessment=overall_assessment,
        overall_risk_level=overall_risk_level,
        confidence=confidence,
        incident_timeline=_parse_list_of_dicts(data.get("incident_timeline")),
        recurring_issues=_parse_list_of_dicts(data.get("recurring_issues")),
        conflicts_or_disputes=_parse_list_of_dicts(data.get("conflicts_or_disputes")),
        critical_red_flags=_parse_list_of_str(data.get("critical_red_flags")),
        positive_signals=_parse_list_of_str(data.get("positive_signals")),
        window_view_summary=window_view_summary,
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ReviewAnalysisService:
    """Orchestrates AI analysis of a unified review corpus.

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

    async def analyse(self, corpus: "ReviewCorpus") -> ReviewAnalysisOutput:
        """Run AI analysis on *corpus* and return structured output.

        Parameters
        ----------
        corpus:
            Unified review corpus with aggregate metadata and comment list.
            At least one comment with a non-empty ``comment_text`` should be
            present for a meaningful analysis; the caller is responsible for
            this check.

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
        prompt = build_reviews_prompt(corpus)
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        logger.debug(
            "Sending review analysis request (%d comments) to OpenRouter",
            len(corpus.comments),
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
