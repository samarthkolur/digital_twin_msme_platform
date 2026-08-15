from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from copilot.service import QueryEngine

_engine: QueryEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _engine
    _engine = QueryEngine()
    try:
        yield
    finally:
        _engine = None


app = FastAPI(title="Digital Cousin Copilot", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


class QueryRequest(BaseModel):
    query: str


class QueryResponseBody(BaseModel):
    answer: str
    used_fallback: bool
    context_size: int


@app.post("/query", response_model=QueryResponseBody)
async def query(request: QueryRequest) -> dict[str, object]:
    assert _engine is not None
    result = await _engine.answer(request.query)
    return {
        "answer": result.answer,
        "used_fallback": result.used_fallback,
        "context_size": result.context_size,
    }
