# Architecture notes

## Why two clusters instead of one

Training and serving have different resource shapes and lifecycles: training jobs are batch, run-to-completion, and want exclusive access to a fixed set of nodes for the job's duration (Slurm's model). Serving is long-lived, request-driven, and wants to scale replica count up and down continuously in response to traffic (Ray Serve's model, or an HPA in Kubernetes). Running both on the same scheduler is possible but usually isn't how production ML platforms are actually built - this repo mirrors that split deliberately: a Slurm partition for training, a separate Ray cluster for serving, connected by a model artifact (the checkpoint the training job produces).

## Local simulation vs. real hardware - what's identical, what's swapped

| Component | This repo (local) | Real deployment |
|---|---|---|
| Slurm nodes | Docker containers on one machine | Physical/VM nodes, e.g. an NVIDIA DGX SuperPOD |
| Training container | Plain Ubuntu + CPU PyTorch | `nvcr.io/nvidia/pytorch` from [NGC](https://catalog.ngc.nvidia.com/), launched via Slurm's Pyxis/Enroot plugin |
| DDP backend | `gloo` (CPU) | `nccl` (GPU, InfiniBand/NVLink-aware) |
| GPU scheduling | `Gres=gpu:0`, `gres.conf` empty | `Gres=gpu:N` + populated `gres.conf` + `ConstrainDevices=yes` |
| Ray nodes | Docker containers on one machine | EC2/GCE instances via `ray_cluster_config.yaml`'s autoscaler |
| GPU metrics | Not available | `dcgm-exporter` (already wired into `monitoring/`, just commented out) |

Nothing else changes: the sbatch script, the DDP training code's structure, the Ray Serve deployment code, and the Prometheus/Grafana config are the same files used in both cases - only the specific lines noted above are swapped.

## Moving to Kubernetes

The JD names Kubernetes, Ray, and Slurm as equivalent options for "scaling ... multi-node cluster configurations." This repo picks Slurm (training) + Ray (serving) because that pairing is exactly how NVIDIA's own reference ML platforms (e.g. NeMo Framework, BioNeMo) are typically deployed. The Kubernetes-native equivalent of the Ray half of this repo is [KubeRay](https://github.com/ray-project/kuberay):

- `ray-cluster/docker-compose.yml` → a `RayCluster` (or `RayService` for the autoscaling Serve deployment) custom resource
- `ray-cluster/serve_app.py` → unchanged; it's deployed the same way, just onto a KubeRay-managed cluster instead of the docker-compose one
- `monitoring/` → the same Prometheus/Grafana stack, typically installed via the `kube-prometheus-stack` Helm chart, scraping the KubeRay pods' `/metrics` via a `ServiceMonitor` instead of static targets
- GPU scheduling → the [NVIDIA GPU Operator](https://github.com/NVIDIA/gpu-operator) instead of raw `gres.conf`, which also installs `dcgm-exporter` as a DaemonSet automatically

The Slurm half of this repo (multi-node distributed training) is the piece Kubernetes is comparatively worse at natively - this is why HPC/AI training clusters (including NVIDIA's own DGX SuperPOD reference architecture) run Slurm even when the serving layer runs on Kubernetes or Ray. Kubeflow's `PyTorchJob`/`MPIJob` CRDs are the closest Kubernetes-native equivalent if a single-scheduler design is required.

## Security notes (what's simplified for the demo, and why)

- **Munge authentication**: real; the controller and compute nodes genuinely authenticate RPCs to each other via a shared munge key, generated at first boot and shared over a Docker named volume (never baked into the image).
- **Cgroup resource containment**: left unconfigured here (no `CgroupPlugin` line, so slurmd autodetects) to keep the demo portable across hosts without needing privileged nested-cgroup access; documented in `slurm-cluster/config/cgroup.conf` as the first thing to re-enable on real hardware.
- **Network segmentation**: the Slurm cluster and the Ray/monitoring stack are on separate Docker networks by default, matching how training and serving environments are commonly segmented in production (see the root README's architecture diagram).
- **Grafana admin password**: hardcoded to `admin`/`admin` via environment variable for local demo convenience only - swap for a secrets-manager-injected value before deploying anywhere reachable outside your own machine.
