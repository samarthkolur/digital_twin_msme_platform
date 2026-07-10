import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from edge.providers import SensorProvider, get_provider

logger = logging.getLogger("edge")

SENSOR_PROVIDER = os.environ.get("SENSOR_PROVIDER", "simulated")

_provider: SensorProvider | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global _provider
    _provider = get_provider(SENSOR_PROVIDER)
    logger.info("edge service started with provider=%s", SENSOR_PROVIDER)
    try:
        yield
    finally:
        _provider.close()
        _provider = None


app = FastAPI(title="Digital Cousin Edge Service", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "provider": SENSOR_PROVIDER}
