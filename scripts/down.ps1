# Tears down all three stacks and the shared network.
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

Push-Location ray-cluster
docker compose down
Pop-Location

Push-Location slurm-cluster
docker compose down -v
Pop-Location

Push-Location monitoring
docker compose down
Pop-Location

try { docker network rm clusternet 2>$null | Out-Null } catch {}

Write-Host "All stacks stopped."
