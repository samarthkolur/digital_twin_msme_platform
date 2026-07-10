#!/usr/bin/env bash
# Validates the host and prepares the local dev environment. After this
# script succeeds, `docker compose watch` is the only other command needed.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[0;33m'; BOLD=$'\033[1m'; RESET=$'\033[0m'
FAILED=0

ok()   { echo "  ${GREEN}✓${RESET} $1"; }
warn() { echo "  ${YELLOW}!${RESET} $1"; }
fail() { echo "  ${RED}✗${RESET} $1"; FAILED=1; }
step() { echo "${BOLD}$1${RESET}"; }

step "==> Docker"
if ! command -v docker >/dev/null 2>&1; then
	fail "Docker is not installed. Install Docker Desktop / Docker Engine: https://docs.docker.com/get-docker/"
elif ! docker info >/dev/null 2>&1; then
	fail "Docker is installed but the daemon isn't reachable (is it running? do you have permission?)"
else
	ok "Docker is installed and reachable ($(docker --version))"
fi

step "==> Docker Compose"
if ! docker compose version >/dev/null 2>&1; then
	fail "Docker Compose v2 plugin not found. It ships with modern Docker Desktop/Engine installs."
else
	ok "Docker Compose available ($(docker compose version --short))"
fi

step "==> Required ports free (1883 mosquitto, 5173 dashboard, 8000 api, 8001 copilot)"
for port in 1883 5173 8000 8001; do
	if command -v lsof >/dev/null 2>&1 && lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
		warn "Port $port is already in use — the matching service will fail to start until it's freed"
	else
		ok "Port $port is free"
	fi
done

step "==> Repository permissions"
if [ -w "$ROOT_DIR" ]; then
	ok "Working directory is writable"
else
	fail "Working directory is not writable: $ROOT_DIR"
fi

step "==> Local .env"
if [ ! -f "$ROOT_DIR/.env" ]; then
	cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
	sed -i.bak "s#/home/CHANGE_ME/.config/digital-cousin/secrets.env#${HOME}/.config/digital-cousin/secrets.env#" "$ROOT_DIR/.env"
	rm -f "$ROOT_DIR/.env.bak"
	ok "Created .env from .env.example"
else
	ok ".env already exists"
fi

# shellcheck disable=SC1091
SECRETS_FILE="$(grep -E '^SECRETS_FILE=' "$ROOT_DIR/.env" | cut -d= -f2-)"
SECRETS_FILE="${SECRETS_FILE:-$HOME/.config/digital-cousin/secrets.env}"

step "==> Secrets file (external to repo): $SECRETS_FILE"
if [ -f "$SECRETS_FILE" ]; then
	ok "Secrets file exists"
else
	mkdir -p "$(dirname "$SECRETS_FILE")"
	cat > "$SECRETS_FILE" <<-'EOF'
	# Digital Cousin copilot API-fallback secrets.
	# Fill in only the provider you intend to use; both are optional
	# (the local TinyLlama/llama.cpp path needs neither).
	ANTHROPIC_API_KEY=
	OPENAI_API_KEY=
	EOF
	chmod 600 "$SECRETS_FILE"
	warn "Created placeholder secrets file at $SECRETS_FILE — fill in keys only if you want the API-fallback copilot path"
fi

step "==> Volumes"
if docker volume inspect digital-cousin_sqlite-data >/dev/null 2>&1; then
	ok "sqlite-data volume already exists"
else
	ok "sqlite-data volume will be created on first 'docker compose up'"
fi

step "==> Git hooks + workspace dependencies (via the toolbox container)"
if [ "$FAILED" -eq 0 ]; then
	docker compose build toolbox
	docker compose run --rm --no-deps toolbox pnpm install --frozen-lockfile
	ok "Installed workspace dependencies and Husky git hooks"
else
	warn "Skipping dependency install — fix the failures above first"
fi

echo
if [ "$FAILED" -eq 0 ]; then
	echo "${GREEN}${BOLD}Bootstrap complete.${RESET} Next: ${BOLD}docker compose watch${RESET}"
else
	echo "${RED}${BOLD}Bootstrap found problems above — fix them and re-run ./scripts/bootstrap.sh${RESET}"
	exit 1
fi
