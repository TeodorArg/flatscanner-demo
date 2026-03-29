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
        Language.RU: "Анализирую объявление — это займёт около 2 минут…",
        Language.EN: "Analysing your listing — this can take around 2 minutes…",
        Language.ES: "Analizando tu anuncio — esto puede tardar unos 2 minutos…",
    },
    "msg.progress.extracting": {
        Language.RU: "Извлекаю данные объявления…",
        Language.EN: "Extracting listing data…",
        Language.ES: "Extrayendo datos del anuncio…",
    },
    "msg.progress.analysing": {
        Language.RU: "Анализирую отзывы и детали объявления…",
        Language.EN: "Analyzing reviews and listing details…",
        Language.ES: "Analizando reseñas y detalles del anuncio…",
    },
    "msg.progress.enriching": {
        Language.RU: "Проверяю район и инфраструктуру…",
        Language.EN: "Checking area and infrastructure…",
        Language.ES: "Verificando zona e infraestructura…",
    },
    "msg.progress.preparing": {
        Language.RU: "Подготавливаю итоговый отчёт…",
        Language.EN: "Preparing final report…",
        Language.ES: "Preparando el informe final…",
    },
    # --- Language switching ---
    "msg.language_set": {
        Language.RU: "Язык изменён на русский.",
        Language.EN: "Language changed to English.",
        Language.ES: "Idioma cambiado a español.",
    },
    "msg.language_invalid": {
        Language.RU: "Неизвестный язык. Используйте: /language ru, /language en, /language es.",
        Language.EN: "Unknown language. Use: /language ru, /language en, /language es.",
        Language.ES: "Idioma desconocido. Use: /language ru, /language en, /language es.",
    },
    # --- Formatter section labels ---
    "fmt.strengths_label": {
        Language.RU: "Плюсы:",
        Language.EN: "Pros:",
        Language.ES: "Ventajas:",
    },
    "fmt.risks_label": {
        Language.RU: "Риски:",
        Language.EN: "Risks:",
        Language.ES: "Riesgos:",
    },
    "fmt.price_label": {
        Language.RU: "Цена:",
        Language.EN: "Price:",
        Language.ES: "Precio:",
    },
    # --- Price verdict labels ---
    "fmt.verdict.fair": {
        Language.RU: "Справедливо",
        Language.EN: "Fair",
        Language.ES: "Justo",
    },
    "fmt.verdict.overpriced": {
        Language.RU: "Завышено",
        Language.EN: "Overpriced",
        Language.ES: "Excesivo",
    },
    "fmt.verdict.underpriced": {
        Language.RU: "Занижено",
        Language.EN: "Underpriced",
        Language.ES: "Asequible",
    },
    "fmt.verdict.unknown": {
        Language.RU: "Неясно",
        Language.EN: "Unknown",
        Language.ES: "Desconocido",
    },
    # --- Reviews section labels ---
    "fmt.reviews_label": {
        Language.RU: "Отзывы:",
        Language.EN: "Reviews:",
        Language.ES: "Reseñas:",
    },
    "fmt.reviews_red_flags_label": {
        Language.RU: "Тревожные сигналы:",
        Language.EN: "Red flags:",
        Language.ES: "Señales de alerta:",
    },
    "fmt.reviews_recurring_label": {
        Language.RU: "Частые проблемы:",
        Language.EN: "Recurring issues:",
        Language.ES: "Problemas recurrentes:",
    },
    "fmt.reviews_disputes_label": {
        Language.RU: "Конфликты:",
        Language.EN: "Disputes:",
        Language.ES: "Conflictos:",
    },
    "fmt.reviews_window_label": {
        Language.RU: "Вид из окна:",
        Language.EN: "Window view:",
        Language.ES: "Vista desde la ventana:",
    },
    # --- Stay-price block ---
    "fmt.stay_price_label": {
        Language.RU: "Стоимость проживания:",
        Language.EN: "Stay price:",
        Language.ES: "Precio de la estancia:",
    },
    "fmt.stay_nights_label": {
        Language.RU: "Ночей:",
        Language.EN: "Nights:",
        Language.ES: "Noches:",
    },
    "fmt.nightly_rate_label": {
        Language.RU: "За ночь:",
        Language.EN: "Per night:",
        Language.ES: "Por noche:",
    },
    "fmt.cleaning_fee_label": {
        Language.RU: "Уборка:",
        Language.EN: "Cleaning fee:",
        Language.ES: "Tarifa de limpieza:",
    },
    "fmt.service_fee_label": {
        Language.RU: "Сервисный сбор:",
        Language.EN: "Service fee:",
        Language.ES: "Tarifa de servicio:",
    },
    # --- Formatter system strings ---
    "fmt.truncated": {
        Language.RU: "\n\n[Сообщение обрезано]",
        Language.EN: "\n\n[Message truncated]",
        Language.ES: "\n\n[Mensaje truncado]",
    },
    # --- Menu: main ---
    "menu.main.title": {
        Language.RU: "Главное меню",
        Language.EN: "Main Menu",
        Language.ES: "Menú principal",
    },
    "menu.main.lang_btn": {
        Language.RU: "🌐 Язык",
        Language.EN: "🌐 Language",
        Language.ES: "🌐 Idioma",
    },
    "menu.main.settings_btn": {
        Language.RU: "⚙️ Настройки",
        Language.EN: "⚙️ Settings",
        Language.ES: "⚙️ Configuración",
    },
    "menu.main.billing_btn": {
        Language.RU: "💳 Оплата",
        Language.EN: "💳 Billing",
        Language.ES: "💳 Facturación",
    },
    "menu.main.help_btn": {
        Language.RU: "❓ Помощь",
        Language.EN: "❓ Help",
        Language.ES: "❓ Ayuda",
    },
    # --- Menu: language screen ---
    "menu.language.title": {
        Language.RU: "Выберите язык:",
        Language.EN: "Choose your language:",
        Language.ES: "Elige tu idioma:",
    },
    "menu.language.selected": {
        Language.RU: "Язык изменён.",
        Language.EN: "Language updated.",
        Language.ES: "Idioma actualizado.",
    },
    "menu.language.ru_btn": {
        Language.RU: "🇷🇺 Русский",
        Language.EN: "🇷🇺 Русский",
        Language.ES: "🇷🇺 Русский",
    },
    "menu.language.en_btn": {
        Language.RU: "🇬🇧 English",
        Language.EN: "🇬🇧 English",
        Language.ES: "🇬🇧 English",
    },
    "menu.language.es_btn": {
        Language.RU: "🇪🇸 Español",
        Language.EN: "🇪🇸 Español",
        Language.ES: "🇪🇸 Español",
    },
    # --- Menu: settings screen ---
    "menu.settings.title": {
        Language.RU: "Настройки",
        Language.EN: "Settings",
        Language.ES: "Configuración",
    },
    "menu.settings.body": {
        Language.RU: "Дополнительные настройки появятся здесь в следующих обновлениях.",
        Language.EN: "Additional settings will appear here in future updates.",
        Language.ES: "La configuración adicional aparecerá aquí en futuras actualizaciones.",
    },
    # --- Menu: billing screen ---
    "menu.billing.title": {
        Language.RU: "Оплата",
        Language.EN: "Billing",
        Language.ES: "Facturación",
    },
    "menu.billing.body": {
        Language.RU: "Тарифные планы и оплата появятся здесь в следующих обновлениях.",
        Language.EN: "Plans and payment options will appear here in future updates.",
        Language.ES: "Los planes y opciones de pago aparecerán aquí en futuras actualizaciones.",
    },
    # --- Menu: help screen ---
    "menu.help.title": {
        Language.RU: "❓ Помощь",
        Language.EN: "❓ Help",
        Language.ES: "❓ Ayuda",
    },
    "menu.help.body": {
        Language.RU: (
            "Отправьте ссылку на объявление об аренде (например, Airbnb) "
            "— я проанализирую его для вас.\n\n"
            "Команды:\n/menu — открыть меню\n/language <код> — сменить язык"
        ),
        Language.EN: (
            "Send a rental listing URL (e.g. Airbnb) "
            "and I'll analyse it for you.\n\n"
            "Commands:\n/menu — open menu\n/language <code> — change language"
        ),
        Language.ES: (
            "Envía una URL de anuncio de alquiler (p. ej. Airbnb) "
            "y lo analizaré para ti.\n\n"
            "Comandos:\n/menu — abrir menú\n/language <código> — cambiar idioma"
        ),
    },
    # --- Menu: shared navigation ---
    "menu.back_btn": {
        Language.RU: "← Назад",
        Language.EN: "← Back",
        Language.ES: "← Volver",
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
