import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from appconfig.schema import AppConfig, AppConfigUpdate, seed_config_from_env
from appconfig.store import ConfigStore

DATABASE_PATH = os.environ.get("DATABASE_PATH", ":memory:")

_store: ConfigStore | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _store
    _store = ConfigStore(DATABASE_PATH, seed_config_from_env())
    try:
        yield
    finally:
        _store.close()
        _store = None


app = FastAPI(title="Digital Cousin Config", lifespan=lifespan)

# Same LAN-only reasoning as api's CORS policy (DD-027): the dashboard reads
# and edits this config from the browser. PATCH is allowed because the
# dashboard's settings panel writes through it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "PATCH"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config", response_model=AppConfig, response_model_by_alias=True)
def get_config() -> AppConfig:
    assert _store is not None
    return _store.get()


@app.patch("/config", response_model=AppConfig, response_model_by_alias=True)
def update_config(update: AppConfigUpdate) -> AppConfig:
    assert _store is not None
    return _store.update(update)
