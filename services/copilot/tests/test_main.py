import pytest
from fastapi.testclient import TestClient

import copilot.main as main_module
from copilot.service import QueryResponse


class _StubEngine:
    async def answer(self, query: str) -> QueryResponse:
        return QueryResponse(
            answer=f"stub answer for: {query}", used_fallback=False, context_size=1
        )


def test_query_endpoint_returns_the_engines_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main_module, "QueryEngine", lambda: _StubEngine())

    with TestClient(main_module.app) as client:
        response = client.post("/query", json={"query": "Is it okay?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "stub answer for: Is it okay?"
    assert body["used_fallback"] is False
    assert body["context_size"] == 1
