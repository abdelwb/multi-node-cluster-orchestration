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

## Troubleshooting: panels show no data at all

Hit this myself: every panel was completely blank, no "No data" message, nothing - because the datasource provisioning file didn't pin a `uid`, so Grafana generated a random one that didn't match the `uid: Prometheus` every panel in `cluster-overview.json` hardcodes. The dashboard JSON loaded fine; its queries just silently never fired (check the browser's network tab for `/api/ds/query` calls - if there are none, this is why).

Fix: `grafana/provisioning/datasources/datasource.yml` must set `uid: Prometheus` explicitly (it does, in this repo - if you copy this setup elsewhere, don't drop that line). After changing it, `docker compose restart grafana` to re-run provisioning.

Also: Grafana's own auto-refresh can be throttled in an automated/backgrounded browser tab - if a panel looks frozen, a full page reload forces it to re-query immediately.

## Note on exact Ray metric names

Ray's exported Prometheus metric names have changed across versions; `ray_serve_num_ongoing_http_requests` is confirmed correct for Ray 2.34.0 (the version pinned in `ray-cluster/docker-compose.yml`). If the "Ray Serve: requests in flight" panel shows no data on a different version, run:

```bash
curl http://localhost:8080/metrics | grep ray_serve
```

against the ray-head container and adjust the panel's query in `grafana/dashboards/cluster-overview.json` to match.
