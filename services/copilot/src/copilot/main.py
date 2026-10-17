import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from copilot.runtime_config import ConfigClient, RuntimeConfig
from copilot.service import QueryEngine

# The copilot is a Phase 2 feature: it answers only while the config service
# reports enablePhase2 (design.md DD-047).
CONFIG_URL = os.environ.get("CONFIG_URL", "http://localhost:8002")

_engine: QueryEngine | None = None
_config: ConfigClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _engine, _config
    _engine = QueryEngine()
    _config = ConfigClient(CONFIG_URL, fallback=RuntimeConfig.from_env())
    try:
        yield
    finally:
        _engine = None
        _config = None


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
    assert _config is not None
    if not _config.get().enable_phase2:
        raise HTTPException(
            status_code=503,
            detail="The copilot is a Phase 2 feature and Phase 2 is disabled (enablePhase2=false).",
        )
    result = await _engine.answer(request.query)
    return {
        "answer": result.answer,
        "used_fallback": result.used_fallback,
        "context_size": result.context_size,
    }
