# ray-cluster

A 3-container multi-node Ray cluster (1 head + 2 workers) serving a model through **Ray Serve** with autoscaling replicas.

## What's here

- `docker-compose.yml` - local multi-node Ray cluster for the demo
- `serve_app.py` - a Ray Serve deployment (`autoscaling_config`: 1→4 replicas) exposing `/predict`
- `load_test.py` - concurrent client that generates enough load to trigger autoscaling and reports latency/throughput
- `ray_cluster_config.yaml` - the Ray **autoscaler** cluster-launcher config for running this on real AWS infrastructure instead of docker-compose, including launching GPU workers straight from an **NVIDIA NGC** container image

## Run it

Bring up the shared network + this stack (or use `../scripts/up.sh`):

```bash
docker network create clusternet   # if not already created by scripts/up.sh
docker compose up -d
```

Install deps and start serving (one-time per container lifetime):

```bash
docker compose exec ray-head pip install -r /home/ray/app/requirements.txt
docker compose exec -d ray-head python /home/ray/app/serve_app.py
```

`exec -d` backgrounds the process inside the container itself (via Docker), so this works the same in PowerShell as it does in bash - a shell-level `&` doesn't.

Load-test it and watch the autoscaler react:

```bash
docker compose exec ray-head python /home/ray/app/load_test.py --requests 1500 --concurrency 20
```

`requests` is already in `requirements.txt`, installed above. Concurrency much above 20 against a single starting replica can queue past the client's 10s timeout before the autoscaler adds capacity - 20 is the value this was actually validated against.

Open http://localhost:8265 (Ray dashboard) during the load test to watch replica count scale from 1 towards 4.

## From this demo to a real cluster

`ray_cluster_config.yaml` is a working Ray autoscaler config for AWS: `ray up ray_cluster_config.yaml` provisions a head node plus GPU worker nodes on demand, with the GPU workers launched directly from `nvcr.io/nvidia/pytorch` (NGC). Swap the `provider`/`available_node_types` block for GCP/Azure/on-prem as needed - the autoscaling and Serve deployment code is unchanged.

See [docs/architecture.md](../docs/architecture.md#moving-to-kubernetes) for the equivalent Kubernetes/KubeRay path.
