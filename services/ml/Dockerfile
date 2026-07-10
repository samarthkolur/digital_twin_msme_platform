# syntax=docker/dockerfile:1
# Training image only — invoked via `docker compose --profile training run ml-trainer`
# (or `make train`). Not part of the default dev/prod service set.

FROM python:3.11-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.5.9 /uv /uvx /usr/local/bin/
ENV UV_LINK_MODE=copy UV_PYTHON=python3.11 PATH="/app/.venv/bin:$PATH"
WORKDIR /app

COPY services/ml/pyproject.toml services/ml/uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-install-project

COPY services/ml ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync

CMD ["uv", "run", "python", "-m", "ml.pipeline"]
