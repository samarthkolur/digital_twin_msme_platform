# Native-Windows stand-in for the Makefile, for hosts without GNU Make
# (WSL2/Git-Bash users should just install make and use the Makefile
# directly instead — this exists only so plain PowerShell works too).
# Keep targets in sync with the Makefile; every line here is a direct
# translation of the corresponding Makefile recipe, no extra logic.
#
# Usage: .\scripts\make.ps1 <target>   e.g. .\scripts\make.ps1 lint

param(
	[Parameter(Mandatory = $true)]
	[string]$Target
)

$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))

function Invoke-Toolbox {
	param([string[]]$InnerArgs)
	& docker compose run --rm --no-deps toolbox @InnerArgs
	if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

switch ($Target) {
	"bootstrap" { & "$PSScriptRoot\bootstrap.ps1" }
	"up" { docker compose up -d }
	"watch" { docker compose watch }
	"down" { docker compose down }
	"build" { docker compose build }
	"logs" { docker compose logs -f }
	"ps" { docker compose ps }
	"clean" { docker compose down --volumes --remove-orphans }

	"lint" {
		Invoke-Toolbox @("pnpm", "run", "lint")
		Invoke-Toolbox @("bash", "-c", 'for d in services/*/; do ruff check "$d"; done')
	}
	"lint-fix" {
		Invoke-Toolbox @("pnpm", "run", "lint:fix")
		Invoke-Toolbox @("bash", "-c", 'for d in services/*/; do ruff check --fix "$d"; done')
	}
	"format" {
		Invoke-Toolbox @("pnpm", "run", "format")
		Invoke-Toolbox @("bash", "-c", 'for d in services/*/; do ruff format "$d"; done')
	}
	"format-check" {
		Invoke-Toolbox @("pnpm", "run", "format:check")
		Invoke-Toolbox @("bash", "-c", 'for d in services/*/; do ruff format --check "$d"; done')
	}
	"typecheck" {
		Invoke-Toolbox @("pnpm", "run", "typecheck")
		Invoke-Toolbox @("bash", "-c", 'for d in services/*/; do (cd "$d" && uv run --group dev mypy .); done')
	}
	"test" {
		Invoke-Toolbox @("pnpm", "run", "test")
		Invoke-Toolbox @("bash", "-c", 'for d in services/*/; do (cd "$d" && uv run --group dev pytest); done')
	}
	"knip" { Invoke-Toolbox @("pnpm", "run", "knip") }

	"train" { docker compose --profile training run --rm ml-trainer }
	"train-synthetic" { docker compose --profile training run --rm ml-trainer uv run python -m ml.pipeline --allow-synthetic }

	"shell-tools" { docker compose run --rm --no-deps toolbox bash }

	default {
		Write-Host "Unknown target: $Target" -ForegroundColor Red
		Write-Host "Available: bootstrap up watch down build logs ps clean lint lint-fix format format-check typecheck test knip train train-synthetic shell-tools"
		exit 1
	}
}
