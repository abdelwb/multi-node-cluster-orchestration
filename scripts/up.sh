#!/usr/bin/env bash
# Brings up the whole demo: shared network, monitoring, Slurm cluster, Ray cluster.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

docker network inspect clusternet >/dev/null 2>&1 || docker network create clusternet

echo "==> monitoring"
(cd monitoring && docker compose up -d)

echo "==> slurm-cluster"
(cd slurm-cluster && docker compose up -d --build)

echo "==> ray-cluster"
(cd ray-cluster && docker compose up -d)

cat <<EOF

All stacks are up.

  Grafana:        http://localhost:3000  (admin/admin)
  Prometheus:     http://localhost:9090
  Ray dashboard:  http://localhost:8265

Next steps are in the root README.md Quickstart section (submit the Slurm
training job, then deploy + load-test the Ray Serve endpoint).
EOF
