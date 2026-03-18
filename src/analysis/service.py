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
from typing import TYPE_CHECKING

from src.analysis.openrouter_client import OpenRouterClient, OpenRouterError
from src.analysis.result import AnalysisResult, PriceVerdict
from src.app.config import Settings
from src.domain.listing import NormalizedListing

if TYPE_CHECKING:
    from src.enrichment.runner import EnrichmentOutcome

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "Ты аналитик по аренде жилья. "
    "Отвечай ТОЛЬКО корректным JSON-объектом без markdown и без пояснений вне JSON. "
    "Все текстовые поля ответа пиши на русском языке. "
    "Используй схему из пользовательского сообщения."
)

_JSON_SCHEMA_HINT = """\
{
  "summary": "<1-2 sentence overview of the listing>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "risks": ["<risk 1>", "<risk 2>"],
  "price_verdict": "fair" | "overpriced" | "underpriced" | "unknown",
  "price_explanation": "<one sentence explaining the price assessment>"
}"""


def build_prompt(
    listing: NormalizedListing,
    enrichment: "EnrichmentOutcome | None" = None,
) -> str:
    """Return a user-turn prompt for the given listing.

    Includes all available structured fields so the model has maximum
    context. Description is capped at 600 characters to control token
    cost.

    Parameters
    ----------
    listing:
        Normalized listing to analyse.
    enrichment:
        Optional enrichment outcome. Successful provider results are
        appended as a structured nearby-context section so the model
        can factor in transport access and local amenities.
    """
    lines: list[str] = ["Проанализируй это объявление об аренде.\n"]

    lines.append(f"Название: {listing.title}")

    if listing.description:
        snippet = listing.description[:600]
        if len(listing.description) > 600:
            snippet += "..."
        lines.append(f"Описание: {snippet}")

    loc = listing.location
    location_parts = [p for p in [loc.neighbourhood, loc.city, loc.country] if p]
    if location_parts:
        lines.append(f"Локация: {', '.join(location_parts)}")

    if listing.price is not None:
        p = listing.price
        lines.append(f"Цена: {p.amount} {p.currency} за {p.period}")
        if p.cleaning_fee is not None:
            lines.append(f"Плата за уборку: {p.cleaning_fee} {p.currency}")

    if listing.bedrooms is not None:
        lines.append(f"Спальни: {listing.bedrooms}")
    if listing.bathrooms is not None:
        lines.append(f"Ванные: {listing.bathrooms}")
    if listing.max_guests is not None:
        lines.append(f"Макс. гостей: {listing.max_guests}")

    if listing.amenities:
        lines.append(f"Удобства: {', '.join(listing.amenities[:15])}")

    if listing.rating is not None:
        lines.append(f"Рейтинг: {listing.rating:.2f} / 5")
    if listing.review_count is not None:
        lines.append(f"Отзывы: {listing.review_count}")

    if listing.host_name:
        host_line = f"Хозяин: {listing.host_name}"
        if listing.host_is_superhost:
            host_line += " (Суперхост)"
        lines.append(host_line)

    if enrichment and enrichment.successes:
        lines.append("\nКонтекст рядом с жильем (из enrichment):")
        for result in enrichment.successes:
            data = result.data or {}
            if result.name == "transport":
                count = data.get("count", 0)
                parts = [f"{count} остановок общественного транспорта в радиусе 500 м"]
                nearest = data.get("nearest_name")
                if nearest:
                    parts.append(f"ближайшая: {nearest!r}")
                lines.append(f"  Транспорт: {', '.join(parts)}")
            elif result.name == "nearby_places":
                count = data.get("count", 0)
                by_cat = data.get("by_category", {})
                cat_str = ", ".join(f"{k}: {v}" for k, v in by_cat.items())
                line = f"  Места рядом: {count} всего в радиусе 500 м"
                if cat_str:
                    line += f" ({cat_str})"
                lines.append(line)

    lines.append(
        f"\nОтветь ТОЛЬКО JSON-объектом, который соответствует этой схеме:\n{_JSON_SCHEMA_HINT}"
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def parse_analysis_response(raw: str) -> AnalysisResult:
    """Parse the model's raw text response into an ``AnalysisResult``.

    The model is instructed to reply with pure JSON. This function is
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
        raise ValueError(f"Expected a JSON object, got {type(data).__name__}")

    # summary is required and must be a non-empty string.
    summary = data.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError(
            "Model response missing required field 'summary' or it is not a non-empty string"
        )

    # strengths and risks must be lists when present.
    strengths_raw = data.get("strengths", [])
    if not isinstance(strengths_raw, list):
        raise ValueError(
            f"'strengths' must be a list, got {type(strengths_raw).__name__}"
        )
    risks_raw = data.get("risks", [])
    if not isinstance(risks_raw, list):
        raise ValueError(f"'risks' must be a list, got {type(risks_raw).__name__}")

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
        summary=summary,
        strengths=[str(s) for s in strengths_raw if isinstance(s, str)],
        risks=[str(r) for r in risks_raw if isinstance(r, str)],
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
        ``openrouter_model`` are used to build the default client.
    client:
        Optional pre-built ``OpenRouterClient``. When provided, *settings*
        is not used to construct the client (useful for testing).
    """

    def __init__(
        self,
        settings: Settings,
        client: OpenRouterClient | None = None,
    ) -> None:
        self._client = client or OpenRouterClient(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
        )

    async def analyse(
        self,
        listing: NormalizedListing,
        enrichment: "EnrichmentOutcome | None" = None,
    ) -> AnalysisResult:
        """Run AI analysis on *listing* and return a structured result.

        Parameters
        ----------
        listing:
            Provider-agnostic normalized listing data.
        enrichment:
            Optional enrichment outcome. Successful provider results are
            included in the prompt so the model can factor in nearby context.

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
        prompt = build_prompt(listing, enrichment)
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
