"""AI analysis orchestration.

``AnalysisService`` is the single entry-point for the analysis stage.
It accepts a ``NormalizedListing``, builds a structured prompt, calls
OpenRouter, parses the JSON response, and returns an ``AnalysisResult``.

The service intentionally keeps the prompt construction and JSON parsing
as plain functions so they can be unit-tested independently.
"""

from __future__ import annotations

import json
import logging

from src.analysis.openrouter_client import OpenRouterClient, OpenRouterError
from src.analysis.result import AnalysisResult, PriceVerdict
from src.app.config import Settings
from src.domain.listing import NormalizedListing

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a rental-property analyst. "
    "Respond ONLY with a valid JSON object — no markdown, no commentary. "
    "Use the schema provided in the user message."
)

_JSON_SCHEMA_HINT = """\
{
  "summary": "<1-2 sentence overview of the listing>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "risks": ["<risk 1>", "<risk 2>"],
  "price_verdict": "fair" | "overpriced" | "underpriced" | "unknown",
  "price_explanation": "<one sentence explaining the price assessment>"
}"""


def build_prompt(listing: NormalizedListing) -> str:
    """Return a user-turn prompt for the given listing.

    Includes all available structured fields so the model has maximum
    context.  Description is capped at 600 characters to control token
    cost.
    """
    lines: list[str] = ["Analyse this rental listing.\n"]

    lines.append(f"Title: {listing.title}")

    if listing.description:
        snippet = listing.description[:600]
        if len(listing.description) > 600:
            snippet += "…"
        lines.append(f"Description: {snippet}")

    loc = listing.location
    location_parts = [
        p
        for p in [loc.neighbourhood, loc.city, loc.country]
        if p
    ]
    if location_parts:
        lines.append(f"Location: {', '.join(location_parts)}")

    if listing.price is not None:
        p = listing.price
        lines.append(
            f"Price: {p.amount} {p.currency} per {p.period}"
        )
        if p.cleaning_fee is not None:
            lines.append(f"Cleaning fee: {p.cleaning_fee} {p.currency}")

    if listing.bedrooms is not None:
        lines.append(f"Bedrooms: {listing.bedrooms}")
    if listing.bathrooms is not None:
        lines.append(f"Bathrooms: {listing.bathrooms}")
    if listing.max_guests is not None:
        lines.append(f"Max guests: {listing.max_guests}")

    if listing.amenities:
        lines.append(f"Amenities: {', '.join(listing.amenities[:15])}")

    if listing.rating is not None:
        lines.append(f"Rating: {listing.rating:.2f} / 5")
    if listing.review_count is not None:
        lines.append(f"Reviews: {listing.review_count}")

    if listing.host_name:
        host_line = f"Host: {listing.host_name}"
        if listing.host_is_superhost:
            host_line += " (Superhost)"
        lines.append(host_line)

    lines.append(f"\nRespond ONLY with JSON matching this schema:\n{_JSON_SCHEMA_HINT}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def parse_analysis_response(raw: str) -> AnalysisResult:
    """Parse the model's raw text response into an ``AnalysisResult``.

    The model is instructed to reply with pure JSON.  This function is
    lenient about leading/trailing whitespace but strict about the JSON
    structure itself.

    Parameters
    ----------
    raw:
        The text content returned by the model.

    Returns
    -------
    AnalysisResult

    Raises
    ------
    ValueError
        If the text cannot be parsed as JSON or does not match the
        expected schema.
    """
    text = raw.strip()

    # Strip a common model habit of wrapping in ```json ... ```
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop first and last fence lines
        inner = lines[1:] if lines[0].startswith("```") else lines
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        text = "\n".join(inner).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model response is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object, got {type(data).__name__}"
        )

    # Coerce price_verdict to enum; fall back to UNKNOWN for unrecognised values.
    raw_verdict = data.get("price_verdict", "unknown")
    try:
        verdict = PriceVerdict(raw_verdict)
    except ValueError:
        logger.warning(
            "Unrecognised price_verdict %r from model; using 'unknown'", raw_verdict
        )
        verdict = PriceVerdict.UNKNOWN

    return AnalysisResult(
        summary=str(data.get("summary", "")),
        strengths=[str(s) for s in data.get("strengths", []) if isinstance(s, str)],
        risks=[str(r) for r in data.get("risks", []) if isinstance(r, str)],
        price_verdict=verdict,
        price_explanation=str(data.get("price_explanation", "")),
    )


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class AnalysisService:
    """Orchestrates the AI analysis of a normalized listing.

    Parameters
    ----------
    settings:
        Application settings; ``openrouter_api_key`` and
        ``openrouter_model`` are used to configure the client.
    """

    def __init__(self, settings: Settings) -> None:
        self._client = OpenRouterClient(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
        )

    async def analyse(self, listing: NormalizedListing) -> AnalysisResult:
        """Run AI analysis on *listing* and return a structured result.

        Parameters
        ----------
        listing:
            Provider-agnostic normalized listing data.

        Returns
        -------
        AnalysisResult

        Raises
        ------
        OpenRouterError
            If the OpenRouter API call fails.
        ValueError
            If the model's response cannot be parsed as a valid
            ``AnalysisResult``.
        """
        prompt = build_prompt(listing)
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        logger.debug(
            "Sending analysis request for listing %s to OpenRouter", listing.id
        )
        raw = await self._client.chat(messages)

        try:
            result = parse_analysis_response(raw)
        except ValueError:
            logger.error(
                "Failed to parse OpenRouter response for listing %s: %r",
                listing.id,
                raw[:200],
            )
            raise

        return result
