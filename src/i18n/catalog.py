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
    # --- Amenities section labels ---
    "fmt.amenities_label": {
        Language.RU: "\u0423\u0434\u043e\u0431\u0441\u0442\u0432\u0430:",
        Language.EN: "Amenities:",
        Language.ES: "Servicios:",
    },
    "fmt.amenities_key_label": {
        Language.RU: "\u041a\u043b\u044e\u0447\u0435\u0432\u044b\u0435 \u0443\u0434\u043e\u0431\u0441\u0442\u0432\u0430:",
        Language.EN: "Key amenities:",
        Language.ES: "Servicios clave:",
    },
    "fmt.amenities_missing_label": {
        Language.RU: "\u041e\u0442\u0441\u0443\u0442\u0441\u0442\u0432\u0443\u0435\u0442 \u0438\u043b\u0438 \u043d\u0435 \u0443\u043a\u0430\u0437\u0430\u043d\u043e:",
        Language.EN: "Missing or not included:",
        Language.ES: "Faltante o no incluido:",
    },
    "fmt.amenities_section.home_comfort": {
        Language.RU: "\u0411\u044b\u0442 \u0438 \u043a\u043e\u043c\u0444\u043e\u0440\u0442:",
        Language.EN: "Home comfort:",
        Language.ES: "Comodidad del hogar:",
    },
    "fmt.amenities_section.kitchen_dining": {
        Language.RU: "\u041a\u0443\u0445\u043d\u044f \u0438 \u0441\u0442\u043e\u043b\u043e\u0432\u0430\u044f:",
        Language.EN: "Kitchen and dining:",
        Language.ES: "Cocina y comedor:",
    },
    "fmt.amenities_section.outdoor_facilities": {
        Language.RU: "\u041d\u0430 \u0443\u043b\u0438\u0446\u0435 \u0438 \u043d\u0430 \u0442\u0435\u0440\u0440\u0438\u0442\u043e\u0440\u0438\u0438:",
        Language.EN: "Outdoor and facilities:",
        Language.ES: "Exterior e instalaciones:",
    },
    # --- Amenity labels ---
    "amenity.wifi": {
        Language.RU: "Wi-Fi",
        Language.EN: "Wi-Fi",
        Language.ES: "Wi-Fi",
    },
    "amenity.kitchen": {
        Language.RU: "\u041a\u0443\u0445\u043d\u044f",
        Language.EN: "Kitchen",
        Language.ES: "Cocina",
    },
    "amenity.air_conditioning": {
        Language.RU: "\u041a\u043e\u043d\u0434\u0438\u0446\u0438\u043e\u043d\u0435\u0440",
        Language.EN: "Air conditioning",
        Language.ES: "Aire acondicionado",
    },
    "amenity.heating": {
        Language.RU: "\u041e\u0442\u043e\u043f\u043b\u0435\u043d\u0438\u0435",
        Language.EN: "Heating",
        Language.ES: "Calefacci\u00f3n",
    },
    "amenity.washer": {
        Language.RU: "\u0421\u0442\u0438\u0440\u0430\u043b\u044c\u043d\u0430\u044f \u043c\u0430\u0448\u0438\u043d\u0430",
        Language.EN: "Washer",
        Language.ES: "Lavadora",
    },
    "amenity.dryer": {
        Language.RU: "\u0421\u0443\u0448\u0438\u043b\u043a\u0430",
        Language.EN: "Dryer",
        Language.ES: "Secadora",
    },
    "amenity.parking": {
        Language.RU: "\u041f\u0430\u0440\u043a\u043e\u0432\u043a\u0430",
        Language.EN: "Parking",
        Language.ES: "Estacionamiento",
    },
    "amenity.pool": {
        Language.RU: "\u0411\u0430\u0441\u0441\u0435\u0439\u043d",
        Language.EN: "Pool",
        Language.ES: "Piscina",
    },
    "amenity.tv": {
        Language.RU: "\u0422\u0412",
        Language.EN: "TV",
        Language.ES: "TV",
    },
    "amenity.balcony": {
        Language.RU: "\u0411\u0430\u043b\u043a\u043e\u043d \u0438\u043b\u0438 \u043f\u0430\u0442\u0438\u043e",
        Language.EN: "Balcony or patio",
        Language.ES: "Balc\u00f3n o patio",
    },
    "amenity.refrigerator": {
        Language.RU: "\u0425\u043e\u043b\u043e\u0434\u0438\u043b\u044c\u043d\u0438\u043a",
        Language.EN: "Refrigerator",
        Language.ES: "Refrigerador",
    },
    "amenity.microwave": {
        Language.RU: "\u041c\u0438\u043a\u0440\u043e\u0432\u043e\u043b\u043d\u043e\u0432\u043a\u0430",
        Language.EN: "Microwave",
        Language.ES: "Microondas",
    },
    "amenity.hot_water": {
        Language.RU: "\u0413\u043e\u0440\u044f\u0447\u0430\u044f \u0432\u043e\u0434\u0430",
        Language.EN: "Hot water",
        Language.ES: "Agua caliente",
    },
    "amenity.bathtub": {
        Language.RU: "\u0412\u0430\u043d\u043d\u0430",
        Language.EN: "Bathtub",
        Language.ES: "Ba\u00f1era",
    },
    "amenity.shampoo": {
        Language.RU: "\u0428\u0430\u043c\u043f\u0443\u043d\u044c",
        Language.EN: "Shampoo",
        Language.ES: "Champ\u00fa",
    },
    "amenity.bidet": {
        Language.RU: "\u0411\u0438\u0434\u0435",
        Language.EN: "Bidet",
        Language.ES: "Bid\u00e9",
    },
    "amenity.hangers": {
        Language.RU: "\u041f\u043b\u0435\u0447\u0438\u043a\u0438",
        Language.EN: "Hangers",
        Language.ES: "Perchas",
    },
    "amenity.bed_linens": {
        Language.RU: "\u041f\u043e\u0441\u0442\u0435\u043b\u044c\u043d\u043e\u0435 \u0431\u0435\u043b\u044c\u0451",
        Language.EN: "Bed linens",
        Language.ES: "Ropa de cama",
    },
    "amenity.cooking_basics": {
        Language.RU: "\u0412\u0441\u0451 \u043d\u0435\u043e\u0431\u0445\u043e\u0434\u0438\u043c\u043e\u0435 \u0434\u043b\u044f \u0433\u043e\u0442\u043e\u0432\u043a\u0438",
        Language.EN: "Cooking basics",
        Language.ES: "Elementos b\u00e1sicos para cocinar",
    },
    "amenity.dishes_and_silverware": {
        Language.RU: "\u041f\u043e\u0441\u0443\u0434\u0430 \u0438 \u0441\u0442\u043e\u043b\u043e\u0432\u044b\u0435 \u043f\u0440\u0438\u0431\u043e\u0440\u044b",
        Language.EN: "Dishes and silverware",
        Language.ES: "Platos y cubiertos",
    },
    "amenity.kettle": {
        Language.RU: "\u0427\u0430\u0439\u043d\u0438\u043a",
        Language.EN: "Kettle",
        Language.ES: "Hervidor",
    },
    "amenity.toaster": {
        Language.RU: "\u0422\u043e\u0441\u0442\u0435\u0440",
        Language.EN: "Toaster",
        Language.ES: "Tostadora",
    },
    "amenity.outdoor_dining": {
        Language.RU: "\u041e\u0431\u0435\u0434\u0435\u043d\u043d\u0430\u044f \u0437\u043e\u043d\u0430 \u043d\u0430 \u0443\u043b\u0438\u0446\u0435",
        Language.EN: "Outdoor dining area",
        Language.ES: "Zona de comedor exterior",
    },
    "amenity.bbq_grill": {
        Language.RU: "\u0413\u0440\u0438\u043b\u044c \u0434\u043b\u044f \u0431\u0430\u0440\u0431\u0435\u043a\u044e",
        Language.EN: "BBQ grill",
        Language.ES: "Parrilla",
    },
    "amenity.smoke_alarm": {
        Language.RU: "\u0414\u0430\u0442\u0447\u0438\u043a \u0434\u044b\u043c\u0430",
        Language.EN: "Smoke alarm",
        Language.ES: "Detector de humo",
    },
    "amenity.carbon_monoxide_alarm": {
        Language.RU: "\u0414\u0430\u0442\u0447\u0438\u043a \u0443\u0433\u0430\u0440\u043d\u043e\u0433\u043e \u0433\u0430\u0437\u0430",
        Language.EN: "Carbon monoxide alarm",
        Language.ES: "Detector de mon\u00f3xido de carbono",
    },
    "amenity.essentials": {
        Language.RU: "\u0411\u0430\u0437\u043e\u0432\u044b\u0435 \u0432\u0435\u0449\u0438",
        Language.EN: "Essentials",
        Language.ES: "Elementos b\u00e1sicos",
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
