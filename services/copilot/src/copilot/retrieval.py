"""Retrieval of recent state objects from `api` (design.md §6.4)."""

import os
from typing import Any

import httpx

API_URL = os.environ.get("API_URL", "http://api:8000")
# design.md §6.4: "the last 10 state objects (covering ~10 seconds of data
# or ~10 historical readings, depending on query type)".
DEFAULT_RETRIEVAL_LIMIT = 10


async def retrieve_recent_states(
    limit: int = DEFAULT_RETRIEVAL_LIMIT,
    client: httpx.AsyncClient | None = None,
) -> list[dict[str, Any]]:
    """Most-recent-first, matching api's own ordering. Returns an empty list
    (not an exception) on a 404 (no data recorded yet) or any request
    failure — an empty retrieval is exactly what should trigger the
    rule-based fallback (design.md §6.4), not a 500 from this service.
    """
    owns_client = client is None
    active_client = client or httpx.AsyncClient(base_url=API_URL, timeout=5.0)
    try:
        response = await active_client.get("/state/history", params={"limit": limit})
        if response.status_code == 404:
            return []
        response.raise_for_status()
        states: list[dict[str, Any]] = response.json()
        return states
    except httpx.HTTPError:
        return []
    finally:
        if owns_client:
            await active_client.aclose()
