# Digital Cousin

A low-cost, retrofittable digital twin platform for MSME legacy machine monitoring. See
[`design.md`](./design.md) for the full product/engineering design — it is the canonical source of
truth for this project (architecture, tech stack, decisions, roadmap, and development log).

## Quick start

Requirements: **Docker** (with Compose v2) and **git**. Nothing else needs to be installed on your
host — Node, pnpm, Python and all dependencies run inside containers.

```sh
git clone https://github.com/samarthkolur/digital_twin_msme_platform.git
cd digital_twin_msme_platform
./scripts/bootstrap.sh
make watch
```

- Dashboard: http://localhost:5173
- API: http://localhost:8000/health
- Config: http://localhost:8002/config
- Copilot (Phase 2 only): http://localhost:8001/health
- MQTT broker: localhost:1883

`make watch` rebuilds/syncs each service automatically as you edit files under
`apps/dashboard/src`, `services/*/src`, etc. It wraps `docker compose watch` and starts the Phase 2
services only when Phase 2 is enabled (below). After pulling new code, run `make build` first so
`make up` doesn't reuse stale images.

## Phase 1 / Phase 2

The project ships in two academic phases, switched by one flag, `enablePhase2`, in the project
config. The config is stored in the SQLite database and served by the `config` service
(`design.md` DD-047):

| `enablePhase2`    | What runs and shows                                                                                                                                                                                                              |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `false` (default) | **Phase 1 — edge monitoring:** sensing, MQTT, storage, the REST API and a dashboard with live readings, trends, temperature alerts and history. ML fields stay empty.                                                            |
| `true`            | **Phase 1 + Phase 2 — AI-enabled digital cousin:** the edge also runs ML inference (anomaly score, health index, model alerts), the copilot service starts, and the dashboard shows the health gauge, ML alerts and the copilot. |

```sh
make config        # show the stored config
make phase2-on     # enable Phase 2 and start its services
make phase2-off    # disable Phase 2 and stop its services (Phase 1 keeps running)
```

You can also flip the flag from the dashboard's **Settings** panel or with `PATCH /config`. The
same config holds the other runtime settings: the publish interval and alert thresholds and, for
Phase 2, the critical-alert fraction and the copilot's language model (`local`/`api`), freshness
window and context size. Running services switch within a few
seconds, without a restart. Starting or stopping the copilot container needs `make up` (or
`make phase2-on` / `make phase2-off`). `ENABLE_PHASE2` in `.env` only seeds a fresh database.
`make train` refuses while Phase 2 is off, since it produces the Phase 2 models.

## Repository layout

```
apps/dashboard/     React + Vite + TypeScript dashboard (offline-first SPA)
services/edge/      Sensor acquisition + feature extraction (Python, FastAPI)
services/api/       REST API over the digital-twin state object (Python, FastAPI)
services/copilot/   Retrieval-grounded NL copilot (Python, FastAPI) — Phase 2
services/config/    Project-wide runtime config incl. enablePhase2 (Python, FastAPI, SQLite)
services/ml/        Offline training pipeline (Isolation Forest, 1D conv autoencoder)
packages/           Shared TypeScript packages (empty until a 2nd TS consumer needs one, DD-013)
docs/architecture/  Standalone architecture docs once a topic outgrows design.md §6
docs/adr/           Standalone ADRs promoted from design.md §15's DD-NNN table
docs/research/       Research notes / evaluation write-ups beyond design.md §8-9
docs/hardware/       Wiring diagrams, datasheets, retrofit notes beyond design.md §6.2
infra/mosquitto/    Local MQTT broker config
docker/             Shared toolbox image (lint/format/typecheck/test, no host installs needed)
scripts/            Bootstrap and validation tooling
```

## Common tasks

All of these run inside Docker — see the [`Makefile`](./Makefile) for the full list.

```sh
make lint          # ESLint + ruff
make format        # Prettier + ruff format
make typecheck      # tsc + mypy
make test           # vitest + pytest (with coverage)
make train           # run the ML training pipeline (profile: training; Phase 2 only)
make phase2-on       # enable Phase 2 (see above); make phase2-off to disable
make shell-tools     # drop into the toolbox container
```

## Secrets

The copilot's optional API-fallback path (Anthropic/OpenAI, used only when local TinyLlama
inference isn't wanted) needs API keys. These are **never** stored in this repository. Instead:

- `scripts/bootstrap.sh` creates `$HOME/.config/digital-cousin/secrets.env` (mode `600`) with
  placeholder keys on first run, and validates it exists on every run.
- The path is configurable via `SECRETS_FILE` in your local `.env` (copied from `.env.example`,
  itself gitignored).
- The default `COPILOT_LLM_MODE=local` needs no secrets at all.

## Production / Raspberry Pi deployment

```sh
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
# with Phase 2 enabled, also start its services:
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile phase2 up -d
```

This switches every image to its `prod` build target, drops dev-only hot reload, and gives the
`edge` service real access to the ADXL345 (SPI) and DS18B20 (1-Wire) sensors instead of the
simulated provider used in local dev. See `services/edge/src/edge/providers/` for the
hardware/simulated provider abstraction.

## Contributing

- Commits follow [Conventional Commits](https://www.conventionalcommits.org/) (enforced by
  commitlint on `commit-msg`).
- `pre-commit` runs lint-staged (ESLint/Prettier/ruff) automatically — see `.husky/`.
- CI (`.github/workflows/ci.yml`) mirrors `make lint`, `make typecheck`, `make test`, Docker builds,
  and security scans (gitleaks, Trivy, CodeQL, dependency audit). All gates must pass before merge.
- Update `design.md` alongside any architectural or dependency change — see `CLAUDE.md` for the
  documentation workflow this repo follows.
