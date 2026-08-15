SHELL := /usr/bin/env bash
COMPOSE := docker compose

.PHONY: bootstrap up watch down build logs ps clean \
	lint lint-fix format format-check typecheck test knip \
	train train-synthetic shell-tools

## Onboarding ---------------------------------------------------------------

bootstrap: ## Validate the host and prepare the local dev environment
	./scripts/bootstrap.sh

up: ## Start the default dev stack in the background
	$(COMPOSE) up -d

watch: ## Start the dev stack with live sync/rebuild (hot reload)
	$(COMPOSE) watch

down: ## Stop and remove the dev stack
	$(COMPOSE) down

build: ## Build all images
	$(COMPOSE) build

logs: ## Tail logs for all services
	$(COMPOSE) logs -f

ps: ## Show running services
	$(COMPOSE) ps

clean: ## Remove containers, networks and dangling volumes for this project
	$(COMPOSE) down --volumes --remove-orphans

## Quality gates (run inside the toolbox container, no host deps required) --

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

train: ## Run the ML training pipeline against the real CWRU dataset (fails until it's downloaded, design.md §24)
	$(COMPOSE) --profile training run --rm ml-trainer

train-synthetic: ## Run the ML training pipeline against synthetic placeholder data (design.md DD-031) — for pipeline dev/demo only, not a calibrated detector
	$(COMPOSE) --profile training run --rm ml-trainer uv run python -m ml.pipeline --allow-synthetic

shell-tools: ## Drop into the toolbox container
	$(COMPOSE) run --rm --no-deps toolbox bash
