# monitoring

Prometheus + Grafana observability stack, wired to scrape the Ray cluster's live metrics and (optionally, on real GPU hardware) NVIDIA DCGM GPU metrics.

## What's here

- `docker-compose.yml` - Prometheus, Grafana (pre-provisioned), node-exporter, and a commented-out `dcgm-exporter` service
- `prometheus.yml` - scrape targets for Ray (all 3 nodes), node-exporter, and (commented) DCGM
- `grafana/provisioning/` - auto-configures the Prometheus datasource and dashboard folder on Grafana startup (no manual clicking required)
- `grafana/dashboards/cluster-overview.json` - host CPU/memory, Ray Serve in-flight requests, and a GPU utilization panel

## Run it

```bash
docker network create clusternet   # if not already created by scripts/up.sh
docker compose up -d
```

Open http://localhost:3000 (`admin`/`admin`) → **Cluster Orchestration → Multi-Node Cluster Overview**. Generate traffic with `../ray-cluster/load_test.py` to see the panels move.

## Enabling real GPU metrics

On a machine with an NVIDIA GPU and the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/) installed:

1. Uncomment the `dcgm-exporter` service in `docker-compose.yml`.
2. Uncomment the `dcgm` job in `prometheus.yml`.
3. Restart: `docker compose up -d`.

The `GPU utilization %` panel in the dashboard starts populating immediately - no dashboard changes needed, the query is already there.

## Note on exact Ray metric names

Ray's exported Prometheus metric names have changed across versions. If the "Ray Serve: requests in flight" panel shows no data, run:

```bash
curl http://localhost:8080/metrics | grep ray_serve
```

against the ray-head container and adjust the panel's query in `grafana/dashboards/cluster-overview.json` to match the metric names your Ray version actually exports.
