# Brings up the whole demo: shared network, monitoring, Slurm cluster, Ray cluster.
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

try {
    docker network inspect clusternet *>$null
} catch {
    docker network create clusternet | Out-Null
}

Write-Host "==> monitoring"
Push-Location monitoring
docker compose up -d
Pop-Location

Write-Host "==> slurm-cluster"
Push-Location slurm-cluster
docker compose up -d --build
Pop-Location

Write-Host "==> ray-cluster"
Push-Location ray-cluster
docker compose up -d
Pop-Location

Write-Host ""
Write-Host "All stacks are up."
Write-Host ""
Write-Host "  Grafana:        http://localhost:3000  (admin/admin)"
Write-Host "  Prometheus:     http://localhost:9090"
Write-Host "  Ray dashboard:  http://localhost:8265"
Write-Host ""
Write-Host "Next steps are in the root README.md Quickstart section (submit the Slurm"
Write-Host "training job, then deploy + load-test the Ray Serve endpoint)."
