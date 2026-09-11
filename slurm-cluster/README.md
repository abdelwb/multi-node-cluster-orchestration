# slurm-cluster

A 3-container multi-node Slurm cluster (1 controller + 2 compute nodes), configured with a real `slurm.conf`/`gres.conf`, running a genuine multi-node PyTorch DDP training job.

## What's here

- `config/slurm.conf` - cluster topology, scheduler, and GPU (`Gres`) declarations for both compute nodes
- `config/gres.conf` - GPU device mapping (empty/commented for this CPU demo; documents exactly what to uncomment on real GPU nodes)
- `config/cgroup.conf` - resource containment config (disabled here; documents the production `ConstrainDevices=yes` setting)
- `Dockerfile` / `entrypoint.sh` - one image, used for both roles; `ROLE=controller` runs `slurmctld`, `ROLE=compute` runs `slurmd`
- `jobs/train_ddp.py` - multi-node PyTorch DDP training script (CPU/`gloo` backend)
- `jobs/submit_distributed_training.sbatch` - the sbatch script that launches it across both nodes, with a commented-out production variant that runs the same job inside an **NVIDIA NGC** PyTorch container via Pyxis/Enroot

## Run it

```bash
docker compose up -d --build
docker compose exec slurmctld sinfo          # confirm both nodes show up as idle
docker compose exec slurmctld sbatch /home/demo/jobs/submit_distributed_training.sbatch
docker compose exec slurmctld squeue         # watch the job run
docker compose exec slurmctld cat /home/demo/jobs/logs/ddp-train-1.out
```

You should see both ranks log process-group initialization, then per-step loss and throughput (samples/sec) - the DDP gradient all-reduce is genuinely happening across the two containers.

## Moving this to a real GPU cluster

1. In `config/slurm.conf`, change each node's `Gres=gpu:0` to its actual GPU count (e.g. `Gres=gpu:8` on a DGX node).
2. In `config/gres.conf`, uncomment the `NodeName=... Name=gpu File=/dev/nvidiaN` lines for each node's devices.
3. In `config/cgroup.conf`, switch to `TaskPlugin=task/cgroup` with `ConstrainDevices=yes` so GPU allocations are actually enforced.
4. In `jobs/submit_distributed_training.sbatch`, use the commented-out `srun --container-image=nvcr.io/nvidia/pytorch:...` block instead of the plain `python3` invocation - this is how Slurm launches containerized jobs from the [NVIDIA NGC catalog](https://catalog.ngc.nvidia.com/) via Pyxis/Enroot on real clusters.
5. In `jobs/train_ddp.py`, change `backend="gloo"` to `backend="nccl"` for GPU collectives.
