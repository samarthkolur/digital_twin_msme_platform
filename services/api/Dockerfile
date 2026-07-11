# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends curl \
	&& rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.5.9 /uv /uvx /usr/local/bin/
ENV UV_LINK_MODE=copy UV_PYTHON=python3.11 PATH="/app/.venv/bin:$PATH"
WORKDIR /app

FROM base AS deps
COPY services/api/pyproject.toml services/api/uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-install-project

FROM deps AS dev
COPY services/api ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --group dev
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "src"]

FROM deps AS prod-deps
COPY services/api/src ./src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-dev

FROM base AS prod
RUN groupadd -r app && useradd -r -g app app
COPY --from=prod-deps /app/.venv /app/.venv
COPY services/api/src ./src
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
