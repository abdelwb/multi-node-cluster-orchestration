#!/usr/bin/env bash
# Tears down all three stacks and the shared network.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

(cd ray-cluster && docker compose down)
(cd slurm-cluster && docker compose down -v)
(cd monitoring && docker compose down)

docker network rm clusternet >/dev/null 2>&1 || true

echo "All stacks stopped."
