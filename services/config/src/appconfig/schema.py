"""The project-wide runtime configuration (design.md DD-047).

Only settings that are safe and useful to change while the stack is running
live here. Bootstrap/infrastructure settings (database path, broker address,
ports, secrets) stay in the environment: a service needs them before it can
reach this config at all.

Field names are camelCase on the wire because the dashboard consumes them
directly; Python code uses the snake_case attribute names.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

# Seeding defaults, also used by every consumer as its fallback when this
# service is unreachable. They match the values the services hard-coded before
# this config existed (design.md §17).
DEFAULT_ENABLE_PHASE2 = False
DEFAULT_PUBLISH_INTERVAL_SECONDS = 5.0
DEFAULT_ALERT_HEALTH_INDEX = 0.6
DEFAULT_ALERT_TEMPERATURE_C = 70.0


class AppConfig(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="forbid", frozen=True
    )

    enable_phase2: bool = Field(
        default=DEFAULT_ENABLE_PHASE2,
        description=(
            "Enables Phase 2 (AI-enabled digital cousin): ML inference on the edge, "
            "the NL copilot and the ML views on the dashboard. Off = Phase 1 only."
        ),
    )
    publish_interval_seconds: float = Field(
        default=DEFAULT_PUBLISH_INTERVAL_SECONDS,
        gt=0,
        le=3600,
        description="Edge acquisition/publish period; the dashboard polls at the same rate.",
    )
    alert_health_index: float = Field(
        default=DEFAULT_ALERT_HEALTH_INDEX,
        ge=0,
        le=1,
        description="Health index below this raises an alert (Phase 2 only: needs ML).",
    )
    alert_temperature_c: float = Field(
        default=DEFAULT_ALERT_TEMPERATURE_C,
        ge=-40,
        le=150,
        description="Surface temperature above this raises an alert.",
    )


class AppConfigUpdate(BaseModel):
    """A partial update: every field optional, same validation as AppConfig."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    enable_phase2: bool | None = None
    publish_interval_seconds: float | None = Field(default=None, gt=0, le=3600)
    alert_health_index: float | None = Field(default=None, ge=0, le=1)
    alert_temperature_c: float | None = Field(default=None, ge=-40, le=150)


_ENV_SEEDS = {
    "enable_phase2": "ENABLE_PHASE2",
    "publish_interval_seconds": "PUBLISH_INTERVAL_SECONDS",
    "alert_health_index": "ALERT_HEALTH_INDEX",
    "alert_temperature_c": "ALERT_TEMPERATURE_C",
}


def seed_config_from_env(environ: dict[str, str] | None = None) -> AppConfig:
    """Initial values for a fresh database: defaults, overridden by any of the
    matching environment variables that are set. Only used to seed keys that
    do not exist yet; after that the database is the source of truth."""
    env = os.environ if environ is None else environ
    overrides = {field: env[var] for field, var in _ENV_SEEDS.items() if env.get(var)}
    return AppConfig.model_validate(overrides)
