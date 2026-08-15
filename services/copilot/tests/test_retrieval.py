import asyncio
import json

import httpx

from copilot.retrieval import retrieve_recent_states


def _client_with_response(status_code: int, body: object) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, content=json.dumps(body))

    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(base_url="http://api:8000", transport=transport)


def test_returns_parsed_states_on_success() -> None:
    body = [{"asset_id": "motor_01", "timestamp": "2026-07-01T09:32:15Z"}]
    client = _client_with_response(200, body)

    states = asyncio.run(retrieve_recent_states(client=client))

    assert states == body


def test_returns_empty_list_on_404() -> None:
    client = _client_with_response(404, {"detail": "not found"})

    states = asyncio.run(retrieve_recent_states(client=client))

    assert states == []


def test_returns_empty_list_on_server_error_rather_than_raising() -> None:
    client = _client_with_response(500, {"detail": "boom"})

    states = asyncio.run(retrieve_recent_states(client=client))

    assert states == []


def test_returns_empty_list_on_connection_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(base_url="http://api:8000", transport=transport)

    states = asyncio.run(retrieve_recent_states(client=client))

    assert states == []
