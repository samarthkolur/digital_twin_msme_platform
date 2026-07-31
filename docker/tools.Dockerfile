# Toolbox image: the single environment for local quality gates (lint, format,
# typecheck, test, git hooks) and for CI. Host machines only need Docker —
# no Node, pnpm, Python, ruff or mypy installation is required to contribute.
FROM node:25-slim

# hadolint ignore=DL3008
RUN apt-get update \
	&& apt-get install -y --no-install-recommends python3.11 python3.11-venv git curl ca-certificates \
	&& rm -rf /var/lib/apt/lists/* \
	&& corepack enable \
	# The repo is bind-mounted from the host (owned by the host user) but this
	# container runs as root, so git's ownership check would otherwise refuse
	# every command with "detected dubious ownership" (lint-staged then just
	# reports "Current directory is not a git directory!"). This container
	# only ever operates on our own bind-mounted repo, so trusting any path is safe.
	&& git config --system --add safe.directory '*'

COPY --from=ghcr.io/astral-sh/uv:0.5.9 /uv /uvx /usr/local/bin/

ENV UV_PYTHON=python3.11 \
	UV_LINK_MODE=copy \
	PATH="/root/.local/bin:$PATH"

# ruff is dependency-free (no project venv needed), so one global, pinned
# version lints/formats every Python service consistently. mypy is installed
# per-service (via each service's pyproject.toml + `uv run`) because type
# checking needs each service's actual dependency graph in scope.
RUN uv tool install ruff==0.8.0

WORKDIR /workspace

CMD ["bash"]
