# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends curl \
	&& rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.5.9 /uv /uvx /usr/local/bin/
ENV UV_LINK_MODE=copy UV_PYTHON=python3.11 PATH="/app/.venv/bin:$PATH"
WORKDIR /app

FROM base AS deps
COPY services/config/pyproject.toml services/config/uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-install-project

FROM deps AS dev
COPY services/config ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --group dev
EXPOSE 8002
CMD ["uv", "run", "uvicorn", "appconfig.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload", "--reload-dir", "src"]

FROM deps AS prod-deps
COPY services/config/src ./src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-dev

FROM base AS prod
RUN groupadd -r app && useradd -r -g app app
COPY --from=prod-deps /app/.venv /app/.venv
COPY services/config/src ./src
USER app
EXPOSE 8002
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s CMD ["sh", "-c", "curl -fsS http://localhost:8002/health || exit 1"]
CMD ["uvicorn", "appconfig.main:app", "--host", "0.0.0.0", "--port", "8002"]
