"""On-demand translation of freeform analysis result blocks.

``TranslationService`` translates the user-facing text fields of an
``AnalysisResult`` (`display_title`, `summary`, `strengths`, `risks`,
`price_explanation`) into the requested language using the LLM.

Design constraints:
- English results are returned as-is without any LLM call.
- Translated output is NOT persisted; it is purely ephemeral.
- The price_verdict enum is language-neutral and is never translated.
- The formatter receives already-translated content plus localized labels.
- The set of translated fields is not hard-coded to the current schema;
  any new freeform text fields can be added to the translation prompt
  without touching this module's caller.
"""

from __future__ import annotations

import json
import logging

from src.analysis.openrouter_client import OpenRouterClient, OpenRouterError
from src.analysis.result import AnalysisResult, ReviewInsightsBlock
from src.app.config import Settings
from src.i18n.types import Language

logger = logging.getLogger(__name__)

# Map Language to a human-readable name used in the translation prompt.
_LANGUAGE_NAME: dict[Language, str] = {
    Language.RU: "Russian",
    Language.EN: "English",
    Language.ES: "Spanish",
}

_TRANSLATION_SCHEMA_HINT = """\
{
  "display_title": "<translated title>",
  "summary": "<translated summary>",
  "strengths": ["<translated strength 1>", "<translated strength 2>"],
  "risks": ["<translated risk 1>", "<translated risk 2>"],
  "price_explanation": "<translated price explanation>",
  "review_overall_assessment": "<translated overall assessment or empty string>",
  "review_critical_red_flags": ["<translated red flag 1>"],
  "review_recurring_issues": ["<translated recurring issue 1>"],
  "review_conflicts_or_disputes": ["<translated dispute 1>"],
  "review_positive_signals": ["<translated positive signal 1>"],
  "review_window_view_summary": "<translated window view summary or empty string>"
}"""


class TranslationError(Exception):
    """Raised when the translation LLM call fails or returns an unparseable response."""


def _build_translation_prompt(result: AnalysisResult, language: Language) -> str:
    """Return the user-turn prompt for translating *result* into *language*."""
    lang_name = _LANGUAGE_NAME[language]
    source: dict = {
        "display_title": result.display_title,
        "summary": result.summary,
        "strengths": result.strengths,
        "risks": result.risks,
        "price_explanation": result.price_explanation,
        "review_overall_assessment": "",
        "review_critical_red_flags": [],
        "review_recurring_issues": [],
        "review_conflicts_or_disputes": [],
        "review_positive_signals": [],
        "review_window_view_summary": "",
    }
    if result.review_insights is not None:
        ri = result.review_insights
        source["review_overall_assessment"] = ri.overall_assessment
        source["review_critical_red_flags"] = ri.critical_red_flags
        source["review_recurring_issues"] = ri.recurring_issues
        source["review_conflicts_or_disputes"] = ri.conflicts_or_disputes
        source["review_positive_signals"] = ri.positive_signals
        source["review_window_view_summary"] = ri.window_view_summary
    return (
        f"Translate the following rental listing analysis fields into {lang_name}.\n"
        "Return ONLY a JSON object matching the output schema.\n"
        "Do not add, remove, or reorder items in lists.\n"
        "Do not alter factual content — translate only.\n\n"
        f"Input:\n{json.dumps(source, ensure_ascii=False, indent=2)}\n\n"
        f"Output schema:\n{_TRANSLATION_SCHEMA_HINT}"
    )


def _coerce_translated_list(
    field_name: str,
    value: object,
    fallback: list[str],
) -> list[str]:
    """Return a sanitized translated text list, logging lossy fallbacks."""
    if not isinstance(value, list):
        logger.warning(
            "Translation response field '%s' was %s; using original list",
            field_name,
            type(value).__name__,
        )
        return fallback

    invalid_items = [item for item in value if not isinstance(item, str)]
    if invalid_items:
        logger.warning(
            "Translation response field '%s' contained %s non-string item(s); dropping them",
            field_name,
            len(invalid_items),
        )

    sanitized = [item for item in value if isinstance(item, str)]
    if not sanitized and value:
        logger.warning(
            "Translation response field '%s' had no usable string items; using original list",
            field_name,
        )
        return fallback
    return sanitized


def _parse_translation_response(raw: str, original: AnalysisResult) -> AnalysisResult:
    """Parse the LLM translation response and merge into a new ``AnalysisResult``.

    The price_verdict is preserved from *original* (it is not translated).
    Fields that cannot be parsed fall back to the original English values.

    Parameters
    ----------
    raw:
        Raw text response from the translation LLM.
    original:
        The canonical English ``AnalysisResult`` used as a fallback.

    Returns
    -------
    AnalysisResult
        A new result with translated freeform fields and the original
        language-neutral verdict.

    Raises
    ------
    TranslationError
        If the text cannot be parsed as JSON or the JSON is not a dict.
    """
    text = raw.strip()

    # Strip optional ```json ... ``` fences that models sometimes add.
    if text.startswith("```"):
        lines = text.splitlines()
        inner = lines[1:]
        if inner and inner[-1].strip() == "```":
            inner = inner[:-1]
        text = "\n".join(inner).strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TranslationError(f"Translation response is not valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise TranslationError(
            f"Translation response must be a JSON object, got {type(data).__name__}"
        )

    display_title = data.get("display_title", original.display_title)
    if not isinstance(display_title, str) or not display_title.strip():
        logger.warning("Translation response missing 'display_title'; using original")
        display_title = original.display_title

    summary = data.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        logger.warning("Translation response missing 'summary'; using original")
        summary = original.summary

    strengths = _coerce_translated_list(
        "strengths",
        data.get("strengths", original.strengths),
        original.strengths,
    )

    risks = _coerce_translated_list(
        "risks",
        data.get("risks", original.risks),
        original.risks,
    )

    price_explanation = data.get("price_explanation", original.price_explanation)
    if not isinstance(price_explanation, str):
        price_explanation = original.price_explanation

    # amenities are scraper labels rendered verbatim — never translated.
    amenities = original.amenities

    # --- Review insights block (optional) ---
    translated_review_insights: ReviewInsightsBlock | None = None
    if original.review_insights is not None:
        ori = original.review_insights
        review_overall_assessment = data.get("review_overall_assessment", ori.overall_assessment)
        if not isinstance(review_overall_assessment, str):
            review_overall_assessment = ori.overall_assessment

        review_window_view_summary = data.get("review_window_view_summary", ori.window_view_summary)
        if not isinstance(review_window_view_summary, str):
            review_window_view_summary = ori.window_view_summary

        review_critical_red_flags = _coerce_translated_list(
            "review_critical_red_flags",
            data.get("review_critical_red_flags", ori.critical_red_flags),
            ori.critical_red_flags,
        )
        review_recurring_issues = _coerce_translated_list(
            "review_recurring_issues",
            data.get("review_recurring_issues", ori.recurring_issues),
            ori.recurring_issues,
        )
        review_conflicts_or_disputes = _coerce_translated_list(
            "review_conflicts_or_disputes",
            data.get("review_conflicts_or_disputes", ori.conflicts_or_disputes),
            ori.conflicts_or_disputes,
        )
        review_positive_signals = _coerce_translated_list(
            "review_positive_signals",
            data.get("review_positive_signals", ori.positive_signals),
            ori.positive_signals,
        )
        translated_review_insights = ReviewInsightsBlock(
            overall_assessment=review_overall_assessment,
            # overall_risk_level is a constrained label (low/medium/high) — not translated.
            overall_risk_level=ori.overall_risk_level,
            review_count=ori.review_count,
            average_rating=ori.average_rating,
            critical_red_flags=review_critical_red_flags,
            recurring_issues=review_recurring_issues,
            conflicts_or_disputes=review_conflicts_or_disputes,
            positive_signals=review_positive_signals,
            window_view_summary=review_window_view_summary,
        )

    return AnalysisResult(
        display_title=display_title,
        summary=summary,
        strengths=strengths,
        risks=risks,
        # price_verdict is language-neutral — never translated.
        price_verdict=original.price_verdict,
        price_explanation=price_explanation,
        amenities=amenities,
        review_insights=translated_review_insights,
    )


class TranslationService:
    """Translates freeform ``AnalysisResult`` blocks into the requested language.

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
        settings: Settings,
        client: OpenRouterClient | None = None,
    ) -> None:
        self._client = client or OpenRouterClient(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
        )

    async def translate(
        self,
        result: AnalysisResult,
        language: Language,
    ) -> AnalysisResult:
        """Return *result* with freeform fields translated into *language*.

        English results are returned as-is without any LLM call.
        Translated output is never persisted.

        Parameters
        ----------
        result:
            Canonical English ``AnalysisResult`` to translate.
        language:
            Target language.

        Returns
        -------
        AnalysisResult
            Original result for English; a new instance with translated
            freeform fields for other languages.

        Raises
        ------
        TranslationError
            If the LLM call fails or the response cannot be parsed.
        OpenRouterError
            If the underlying HTTP call to OpenRouter fails.
        """
        if language is Language.EN:
            return result

        prompt = _build_translation_prompt(result, language)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a professional translator. "
                    "Reply ONLY with a valid JSON object, no markdown, no text outside the JSON."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        logger.debug("Requesting translation to %s", language.value)
        try:
            raw = await self._client.chat(messages)
        except OpenRouterError:
            logger.error("OpenRouter call failed during translation to %s", language.value)
            raise

        try:
            return _parse_translation_response(raw, original=result)
        except TranslationError:
            logger.error(
                "Failed to parse translation response for language %s: %r",
                language.value,
                raw[:200],
            )
            raise
