"""Minimal Apify HTTP client.

Runs an Apify actor synchronously and returns the resulting dataset items.
The client is intentionally narrow: it only supports the
``run-sync-get-dataset-items`` endpoint, which is the right choice for
short-lived, single-listing extraction tasks.

Usage
-----
    client = ApifyClient(api_token="...", actor_id="dtrungtin~airbnb-scraper")
    items = await client.run_and_get_items({"startUrls": [{"url": url}]})
"""

from __future__ import annotations

from typing import Any

import httpx

APIFY_BASE_URL = "https://api.apify.com/v2"

# Default timeout for synchronous actor runs (seconds).  Airbnb scrapes are
# typically fast but the actor cold-start can take up to ~30 s.
DEFAULT_TIMEOUT = 120.0


class ApifyError(Exception):
    """Raised when the Apify API returns an error or an unexpected response."""


class ApifyClient:
    """Thin async wrapper around the Apify REST API.

    Parameters
    ----------
    api_token:
        Apify personal API token (APIFY_API_TOKEN env variable).
    actor_id:
        Actor identifier in ``username~actor-name`` or numeric ID form.
    timeout:
        HTTP request timeout in seconds (default 120).
    """

    def __init__(
        self,
        api_token: str,
        actor_id: str,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._api_token = api_token
        self._actor_id = actor_id
        self._timeout = timeout

    async def run_and_get_items(
        self, input_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Run the actor with *input_data* and return the dataset items.

        Uses the ``run-sync-get-dataset-items`` endpoint so the HTTP call
        blocks until the actor finishes (or the timeout is hit).

        Parameters
        ----------
        input_data:
            JSON-serialisable actor input dict.

        Returns
        -------
        list[dict[str, Any]]
            The list of items from the actor's default dataset.

        Raises
        ------
        ApifyError
            If the API returns a non-200 status or an unexpected body.
        httpx.TimeoutException
            If the actor does not finish within *timeout* seconds.
        """
        url = (
            f"{APIFY_BASE_URL}/acts/{self._actor_id}"
            f"/run-sync-get-dataset-items"
        )
        headers = {"Authorization": f"Bearer {self._api_token}"}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, headers=headers, json=input_data)

        if not (200 <= response.status_code < 300):
            raise ApifyError(
                f"Apify actor run failed with status {response.status_code}: "
                f"{response.text[:400]}"
            )

        body = response.json()
        if not isinstance(body, list):
            raise ApifyError(
                f"Unexpected Apify response type: expected list, "
                f"got {type(body).__name__}"
            )

        return body
