# Validates the host and prepares the local dev environment on native Windows
# (PowerShell, no WSL/Git Bash required). Mirrors scripts/bootstrap.sh exactly
# — see that file for the canonical logic; keep both in sync when either
# changes. After this script succeeds, `docker compose watch` is the only
# other command needed.

$ErrorActionPreference = "Continue"
$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RootDir

$script:Failed = $false

function Write-Ok { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  [!] $msg" -ForegroundColor Yellow }
function Write-Fail { param($msg) Write-Host "  [X] $msg" -ForegroundColor Red; $script:Failed = $true }
function Write-Step { param($msg) Write-Host $msg -ForegroundColor White }

Write-Step "==> Docker"
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
	Write-Fail "Docker is not installed. Install Docker Desktop: https://docs.docker.com/get-docker/"
} else {
	docker info *> $null
	if ($LASTEXITCODE -ne 0) {
		Write-Fail "Docker is installed but the daemon isn't reachable (is Docker Desktop running?)"
	} else {
		$dockerVersion = (docker --version)
		Write-Ok "Docker is installed and reachable ($dockerVersion)"
	}
}

Write-Step "==> Docker Compose"
docker compose version *> $null
if ($LASTEXITCODE -ne 0) {
	Write-Fail "Docker Compose v2 plugin not found. It ships with modern Docker Desktop installs."
} else {
	$composeVersion = (docker compose version --short)
	Write-Ok "Docker Compose available ($composeVersion)"
}

Write-Step "==> Required ports free (1883 mosquitto, 5173 dashboard, 8000 api, 8001 copilot)"
foreach ($port in 1883, 5173, 8000, 8001) {
	$inUse = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
	if ($inUse) {
		Write-Warn "Port $port is already in use — the matching service will fail to start until it's freed"
	} else {
		Write-Ok "Port $port is free"
	}
}

Write-Step "==> Repository permissions"
try {
	$probe = Join-Path $RootDir ".bootstrap-write-probe"
	[IO.File]::WriteAllText($probe, "")
	Remove-Item $probe -Force
	Write-Ok "Working directory is writable"
} catch {
	Write-Fail "Working directory is not writable: $RootDir"
}

Write-Step "==> Local .env"
$envPath = Join-Path $RootDir ".env"
$envExamplePath = Join-Path $RootDir ".env.example"
if (-not (Test-Path $envPath)) {
	Copy-Item $envExamplePath $envPath
	# .env.example's default SECRETS_FILE is a Unix path (for scripts/bootstrap.sh
	# on Linux/macOS/WSL); on native Windows point it at the user profile instead,
	# using forward slashes so Docker Desktop resolves it as a bind-mount path.
	$winSecretsDefault = (Join-Path $env:USERPROFILE ".config/digital-cousin/secrets.env") -replace '\\', '/'
	(Get-Content $envPath) `
		-replace '/home/CHANGE_ME/\.config/digital-cousin/secrets\.env', $winSecretsDefault |
		Set-Content $envPath
	Write-Ok "Created .env from .env.example"
} else {
	Write-Ok ".env already exists"
}

$secretsLine = (Get-Content $envPath | Where-Object { $_ -match '^SECRETS_FILE=' })
$secretsFile = if ($secretsLine) { ($secretsLine -split '=', 2)[1] } else { "" }
if ([string]::IsNullOrWhiteSpace($secretsFile)) {
	$secretsFile = (Join-Path $env:USERPROFILE ".config/digital-cousin/secrets.env") -replace '\\', '/'
}

Write-Step "==> Secrets file (external to repo): $secretsFile"
if (Test-Path $secretsFile) {
	Write-Ok "Secrets file exists"
} else {
	New-Item -ItemType Directory -Force -Path (Split-Path $secretsFile) | Out-Null
	@"
# Digital Cousin copilot API-fallback secrets.
# Fill in only the provider you intend to use; both are optional
# (the local TinyLlama/llama.cpp path needs neither).
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
"@ | Set-Content $secretsFile
	Write-Warn "Created placeholder secrets file at $secretsFile — fill in keys only if you want the API-fallback copilot path"
}

Write-Step "==> Volumes"
docker volume inspect digital-cousin_sqlite-data *> $null
if ($LASTEXITCODE -eq 0) {
	Write-Ok "sqlite-data volume already exists"
} else {
	Write-Ok "sqlite-data volume will be created on first 'docker compose up'"
}

Write-Step "==> Git hooks + workspace dependencies (via the toolbox container)"
if (-not $script:Failed) {
	docker compose build toolbox
	docker compose run --rm --no-deps toolbox pnpm install --frozen-lockfile
	Write-Ok "Installed workspace dependencies and Husky git hooks"
} else {
	Write-Warn "Skipping dependency install — fix the failures above first"
}

Write-Host ""
if (-not $script:Failed) {
	Write-Host "Bootstrap complete. Next: docker compose watch" -ForegroundColor Green
} else {
	Write-Host "Bootstrap found problems above — fix them and re-run .\scripts\bootstrap.ps1" -ForegroundColor Red
	exit 1
}
