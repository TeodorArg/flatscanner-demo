"""Static bot/system string catalog and lookup helper.

All user-facing bot strings that are not AI-generated freeform blocks live
here.  AI-generated freeform blocks (summary, strengths, risks, etc.) are
kept in English in the analysis result and translated separately by the
translation stage.

Usage::

    from src.i18n.catalog import get_string
    from src.i18n.types import Language

    text = get_string("msg.help", Language.RU)
"""

from __future__ import annotations

from src.i18n.types import DEFAULT_LANGUAGE, Language

# Catalog of static bot/system strings.
# Keys use dot-separated namespacing: "<namespace>.<identifier>".
# Every key MUST have an entry for DEFAULT_LANGUAGE (Russian).
_CATALOG: dict[str, dict[Language, str]] = {
    "msg.help": {
        Language.RU: (
            "Пожалуйста, отправьте ссылку на объявление об аренде "
            "(например, ссылку на Airbnb), и я проанализирую его для вас."
        ),
        Language.EN: (
            "Please send a rental listing URL (e.g. an Airbnb link) "
            "and I'll analyse it for you."
        ),
        Language.ES: (
            "Por favor, envía una URL de anuncio de alquiler "
            "(por ejemplo, un enlace de Airbnb) y lo analizaré para ti."
        ),
    },
    "msg.unsupported": {
        Language.RU: (
            "Извините, этот провайдер объявлений пока не поддерживается. "
            "Пожалуйста, отправьте ссылку на Airbnb."
        ),
        Language.EN: (
            "Sorry, I don't support that listing provider yet. "
            "Please send an Airbnb link."
        ),
        Language.ES: (
            "Lo siento, ese proveedor de anuncios aún no es compatible. "
            "Por favor, envía un enlace de Airbnb."
        ),
    },
    "msg.analysing": {
        Language.RU: (
            "Понял! Анализирую объявление по ссылке {url} — "
            "скоро вернусь с результатами."
        ),
        Language.EN: (
            "Got it! I'm looking at the listing at {url} — "
            "I'll get back to you shortly."
        ),
        Language.ES: (
            "¡Entendido! Estoy analizando el anuncio en {url} — "
            "te responderé en breve."
        ),
    },
}


def get_string(key: str, lang: Language) -> str:
    """Return the catalog string for *key* in *lang*.

    Falls back to ``DEFAULT_LANGUAGE`` when *lang* has no entry for *key*.

    Parameters
    ----------
    key:
        Dot-separated catalog key, e.g. ``"msg.help"``.
    lang:
        Requested output language.

    Raises
    ------
    KeyError
        If *key* is not present in the catalog at all.
    """
    entry = _CATALOG.get(key)
    if entry is None:
        raise KeyError(f"Unknown i18n key: {key!r}")
    value = entry.get(lang)
    return value if value is not None else entry[DEFAULT_LANGUAGE]
