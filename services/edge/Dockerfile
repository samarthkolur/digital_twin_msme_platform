# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends curl \
	&& rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.5.9 /uv /uvx /usr/local/bin/
ENV UV_LINK_MODE=copy UV_PYTHON=python3.11 PATH="/app/.venv/bin:$PATH"
WORKDIR /app

FROM base AS deps
COPY services/edge/pyproject.toml services/edge/uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-install-project

# --- dev: hot-reload via uvicorn --reload, used by `docker compose watch` --
FROM deps AS dev
COPY services/edge ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --group dev
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "edge.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "src"]

# --- prod: slim runtime image, non-root, no dev deps ------------------------
FROM deps AS prod-deps
COPY services/edge/src ./src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-dev

FROM base AS prod
RUN groupadd -r app && useradd -r -g app app
COPY --from=prod-deps /app/.venv /app/.venv
COPY services/edge/src ./src
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["uvicorn", "edge.main:app", "--host", "0.0.0.0", "--port", "8000"]
