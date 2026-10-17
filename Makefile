SHELL := /usr/bin/env bash
COMPOSE := docker compose

.PHONY: bootstrap up watch down build logs ps clean \
	config phase2-on phase2-off \
	lint lint-fix format format-check typecheck test knip \
	train train-synthetic shell-tools

# Compose profiles implied by the stored config (design.md DD-047): "phase2"
# when enablePhase2 is on, nothing otherwise. Read through the config service's
# CLI so the database stays the single source of truth.
CONFIG_CLI := $(COMPOSE) run --rm --no-deps -T config python -m appconfig.cli
ALL_PROFILES := --profile phase2 --profile training

# Prints the profiles on stdout and nothing else. The config image is built
# first, quietly: when `run` has to build it, build output can reach stdout
# and would be mistaken for a profile name.
define read_profiles
$(COMPOSE) build -q config >&2 && $(CONFIG_CLI) profiles | tail -n 1
endef

# Starts the stack for the stored phase. With Phase 2 off, a copilot left over
# from an earlier Phase 2 run is stopped, so only Phase 1 is up.
define start_for_phase
	@profiles="$$($(read_profiles))" || exit 1; \
	case "$$profiles" in ""|phase2) ;; \
		*) echo "unexpected compose profiles from the config CLI: '$$profiles'" >&2; exit 1;; esac; \
	echo "enablePhase2 -> compose profiles: $${profiles:-(none, Phase 1 only)}"; \
	if [ -z "$$profiles" ]; then $(COMPOSE) $(ALL_PROFILES) rm -sf copilot; fi; \
	COMPOSE_PROFILES="$$profiles" $(COMPOSE) $(1)
endef

## Onboarding ---------------------------------------------------------------

bootstrap: ## Validate the host and prepare the local dev environment
	./scripts/bootstrap.sh

up: ## Start the dev stack in the background (Phase 2 services only if enablePhase2)
	$(call start_for_phase,up -d)

watch: ## Start the dev stack with live sync/rebuild (Phase 2 services only if enablePhase2)
	$(call start_for_phase,watch)

down: ## Stop and remove the dev stack, Phase 2 services included
	$(COMPOSE) $(ALL_PROFILES) down

## Project config (design.md DD-047) -----------------------------------------

config: ## Show the stored project config
	$(CONFIG_CLI) show

phase2-on: ## Enable Phase 2 (ML inference, copilot, ML dashboard views) and start its services
	$(CONFIG_CLI) set enablePhase2 true
	$(call start_for_phase,up -d)

phase2-off: ## Disable Phase 2 and stop its services, leaving Phase 1 running
	$(CONFIG_CLI) set enablePhase2 false
	$(call start_for_phase,up -d)

build: ## Build all images
	$(COMPOSE) build

logs: ## Tail logs for all services
	$(COMPOSE) logs -f

ps: ## Show running services
	$(COMPOSE) ps

clean: ## Remove containers, networks and dangling volumes for this project
	$(COMPOSE) down --volumes --remove-orphans

## Quality gates (run inside the toolbox container, no host deps required) --

# Run the toolbox as the host user so nothing it writes through the bind mount
# comes back root-owned (design.md DD-039).
export TOOLBOX_UID := $(shell id -u)
export TOOLBOX_GID := $(shell id -g)

TOOLBOX := $(COMPOSE) run --rm --no-deps toolbox

lint: ## Lint TypeScript + Python
	$(TOOLBOX) pnpm run lint
	$(TOOLBOX) bash -c 'for d in services/*/; do ruff check "$$d"; done'

lint-fix: ## Lint and auto-fix TypeScript + Python
	$(TOOLBOX) pnpm run lint:fix
	$(TOOLBOX) bash -c 'for d in services/*/; do ruff check --fix "$$d"; done'

format: ## Format the whole repo
	$(TOOLBOX) pnpm run format
	$(TOOLBOX) bash -c 'for d in services/*/; do ruff format "$$d"; done'

format-check: ## Check formatting without writing
	$(TOOLBOX) pnpm run format:check
	$(TOOLBOX) bash -c 'for d in services/*/; do ruff format --check "$$d"; done'

typecheck: ## Type-check TypeScript (tsc) + Python (mypy)
	$(TOOLBOX) pnpm run typecheck
	$(TOOLBOX) bash -c 'for d in services/*/; do (cd "$$d" && uv run --group dev mypy .); done'

test: ## Run all test suites with coverage
	$(TOOLBOX) pnpm run test
	$(TOOLBOX) bash -c 'for d in services/*/; do (cd "$$d" && uv run --group dev pytest); done'

knip: ## Detect unused deps/exports/dead files in the TS workspace
	$(TOOLBOX) pnpm run knip

# Training produces the Phase 2 models, so it refuses while Phase 2 is off.
define require_phase2
	@if [ -z "$$($(read_profiles))" ]; then \
		echo "Phase 2 is disabled (enablePhase2=false). Run 'make phase2-on' first."; exit 1; \
	fi
endef

train: ## Run the ML training pipeline against the real CWRU dataset (Phase 2; fails until it's downloaded, design.md §24)
	$(require_phase2)
	$(COMPOSE) --profile training run --rm ml-trainer

train-synthetic: ## Run the ML training pipeline against synthetic placeholder data (Phase 2; design.md DD-031) — for pipeline dev/demo only, not a calibrated detector
	$(require_phase2)
	$(COMPOSE) --profile training run --rm ml-trainer uv run python -m ml.pipeline --allow-synthetic

shell-tools: ## Drop into the toolbox container
	$(COMPOSE) run --rm --no-deps toolbox bash
