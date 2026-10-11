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
docker compose watch
```

### Windows

`docker compose watch`/`up`/`down`/`build`/`logs`/`ps` are plain Docker CLI calls and already work
identically in PowerShell, cmd, or a WSL2/Git Bash shell — no changes needed. The two things that
don't work out of the box on a stock Windows install are `scripts/bootstrap.sh` (bash) and every
`make ...` target (GNU Make isn't bundled with Windows). Pick one:

- **WSL2 (recommended)** — install [Docker Desktop with the WSL2
  backend](https://docs.docker.com/desktop/wsl/), clone the repo _inside_ the WSL2 filesystem (not
  under `/mnt/c/...`), and follow the Quick start above unmodified inside the WSL2 shell. This gives
  full parity with Linux/macOS, including `make`.
- **Native PowerShell (no WSL)** — use the PowerShell equivalents committed alongside the bash/Make
  originals:

  ```powershell
  git clone https://github.com/samarthkolur/digital_twin_msme_platform.git
  cd digital_twin_msme_platform
  .\scripts\bootstrap.ps1
  docker compose watch
  ```

  For the quality-gate commands normally run via `make` (see below), use
  `.\scripts\make.ps1 <target>` instead, e.g. `.\scripts\make.ps1 lint`. `scripts/bootstrap.ps1` and
  `scripts/make.ps1` are line-for-line translations of `scripts/bootstrap.sh` and the `Makefile` —
  keep all of them in sync if either changes (design.md DD-038).

- Dashboard: http://localhost:5173
- API: http://localhost:8000/health
- Copilot: http://localhost:8001/health
- MQTT broker: localhost:1883

`docker compose watch` rebuilds/syncs each service automatically as you edit files under
`apps/dashboard/src`, `services/*/src`, etc.

## Repository layout

```
apps/dashboard/     React + Vite + TypeScript dashboard (offline-first SPA)
services/edge/      Sensor acquisition + feature extraction (Python, FastAPI)
services/api/       REST API over the digital-twin state object (Python, FastAPI)
services/copilot/   Retrieval-grounded NL copilot (Python, FastAPI)
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

All of these run inside Docker — see the [`Makefile`](./Makefile) for the full list. On native
Windows without `make` (see [Windows](#windows) above), run the same targets via
`.\scripts\make.ps1 <target>` instead.

```sh
make lint          # ESLint + ruff
make format        # Prettier + ruff format
make typecheck      # tsc + mypy
make test           # vitest + pytest (with coverage)
make train           # run the ML training pipeline (profile: training)
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
