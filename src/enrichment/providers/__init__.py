"""Default enrichment provider set for MVP.

``build_default_providers`` constructs the Geoapify transport and
nearby-places providers when ``settings.geoapify_api_key`` is set.
Returns an empty list when the key is absent so enrichment is skipped
gracefully without breaking the pipeline.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.enrichment.providers.geoapify_nearby_places import (
    GeoapifyNearbyPlacesProvider,
)
from src.enrichment.providers.geoapify_transport import GeoapifyTransportProvider

if TYPE_CHECKING:
    from src.app.config import Settings
    from src.enrichment.runner import EnrichmentProvider


def build_default_providers(settings: "Settings") -> "list[EnrichmentProvider]":
    """Return the default enrichment providers for production use.

    Returns an empty list when ``settings.geoapify_api_key`` is not set so
    enrichment is skipped gracefully without altering the pipeline.

    Parameters
    ----------
    settings:
        Application settings.

    Returns
    -------
    list[EnrichmentProvider]
        ``[GeoapifyTransportProvider, GeoapifyNearbyPlacesProvider]`` when a
        key is configured; ``[]`` otherwise.
    """
    if not settings.geoapify_api_key:
        return []
    return [
        GeoapifyTransportProvider(api_key=settings.geoapify_api_key),
        GeoapifyNearbyPlacesProvider(api_key=settings.geoapify_api_key),
    ]
