import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from api.storage import StateReader

ASSET_ID = os.environ.get("ASSET_ID", "motor_01")
DATABASE_PATH = os.environ.get("DATABASE_PATH", ":memory:")

_reader: StateReader | None = None


class VibrationFeaturesResponse(BaseModel):
    rms_g: float
    kurtosis: float
    crest_factor: float
    peak_to_peak_g: float
    sampling_hz: int


class StateResponse(BaseModel):
    asset_id: str
    timestamp: str
    vibration: VibrationFeaturesResponse
    temperature_c: float
    anomaly_score: float | None
    health_index: float | None
    model_confidence: str | None
    alert_level: str | None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _reader
    _reader = StateReader(DATABASE_PATH)
    try:
        yield
    finally:
        _reader.close()
        _reader = None


app = FastAPI(title="Digital Cousin API", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/state/current", response_model=StateResponse)
def get_current_state(asset_id: str = ASSET_ID) -> dict[str, object]:
    assert _reader is not None
    state = _reader.latest(asset_id)
    if state is None:
        raise HTTPException(
            status_code=404, detail=f"No state recorded yet for asset_id={asset_id!r}"
        )
    return state


@app.get("/state/history", response_model=list[StateResponse])
def get_state_history(
    asset_id: str = ASSET_ID,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict[str, object]]:
    assert _reader is not None
    return _reader.history(asset_id, limit=limit)
