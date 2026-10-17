# Toolbox image: the single environment for local quality gates (lint, format,
# typecheck, test, git hooks). Host machines only need Docker — no Node, pnpm,
# Python, ruff or mypy installation is required to contribute.
#
# This image is built to run as an arbitrary UID/GID, not just root. The repo is
# bind-mounted, so anything the container writes (coverage reports, caches,
# formatted files, git objects created by the pre-commit hook) lands on the host
# owned by whoever the container ran as. Running as root left root-owned files
# across the worktree and inside .git, which then broke subsequent git commands
# for the host user (design.md DD-039). Callers pass the host UID/GID via
# TOOLBOX_UID/TOOLBOX_GID; everything below keeps that workable.
FROM node:22-slim

# Caches and tool installs must live somewhere a non-root, non-"node" UID can
# write, so HOME is moved off /root and made world-writable below.
ENV TOOLBOX_HOME=/opt/toolbox-home
ENV HOME="${TOOLBOX_HOME}" \
	XDG_CACHE_HOME="${TOOLBOX_HOME}/.cache" \
	XDG_DATA_HOME="${TOOLBOX_HOME}/.local/share" \
	COREPACK_HOME="${TOOLBOX_HOME}/.cache/node/corepack" \
	npm_config_cache="${TOOLBOX_HOME}/.npm" \
	UV_PYTHON=python3.11 \
	UV_LINK_MODE=copy \
	UV_TOOL_BIN_DIR=/usr/local/bin \
	PATH="/usr/local/bin:${PATH}"

# hadolint ignore=DL3008
RUN apt-get update \
	&& apt-get install -y --no-install-recommends python3.11 python3.11-venv git curl ca-certificates \
	&& rm -rf /var/lib/apt/lists/* \
	# The repo is bind-mounted from the host, so git's ownership check would
	# otherwise refuse every command with "detected dubious ownership". This
	# container only ever operates on our own bind-mounted repo.
	&& git config --system --add safe.directory '*'

COPY --from=ghcr.io/astral-sh/uv:0.5.9 /uv /uvx /usr/local/bin/

# ruff is dependency-free (no project venv needed), so one global, pinned
# version lints/formats every Python service consistently. mypy is installed
# per-service (via each service's pyproject.toml + `uv run`) because type
# checking needs each service's actual dependency graph in scope.
#
# pnpm is baked in rather than downloaded by corepack on every run: a non-root
# UID cannot write to a root-owned corepack cache, and it saves a download per
# invocation. Keep the version in step with package.json's `packageManager`.
RUN mkdir -p "${TOOLBOX_HOME}" \
	&& corepack enable \
	&& corepack prepare pnpm@11.11.0 --activate \
	&& uv tool install ruff==0.8.0 \
	&& chmod -R 0777 "${TOOLBOX_HOME}"

WORKDIR /workspace

CMD ["bash"]
