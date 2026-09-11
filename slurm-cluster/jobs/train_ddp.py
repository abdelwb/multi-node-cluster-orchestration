"""
Minimal multi-node PyTorch DistributedDataParallel (DDP) training job.

Launched once per Slurm task (one process per compute node here) by
submit_distributed_training.sbatch, with rank/world-size/rendezvous info
passed in from Slurm's own environment variables (SLURM_PROCID, SLURM_NTASKS,
etc.) - the same pattern used to launch real multi-node training jobs on
NVIDIA DGX/Slurm clusters, just with a "gloo" CPU backend swapped in for the
"nccl" GPU backend.

This intentionally trains on synthetic data - the point is to exercise (and
let you observe) real multi-node process-group formation, gradient
synchronization, and per-step throughput, which is exactly what "performance
monitoring and analysis" means for a distributed training job.
"""
import argparse
import os
import time

import torch
import torch.distributed as dist
import torch.nn as nn


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--rank", type=int, required=True)
    p.add_argument("--world-size", type=int, required=True)
    p.add_argument("--master-addr", type=str, required=True)
    p.add_argument("--master-port", type=str, required=True)
    p.add_argument("--steps", type=int, default=50)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--dim", type=int, default=1024)
    return p.parse_args()


def main():
    args = parse_args()

    os.environ["MASTER_ADDR"] = args.master_addr
    os.environ["MASTER_PORT"] = str(args.master_port)
    os.environ["RANK"] = str(args.rank)
    os.environ["WORLD_SIZE"] = str(args.world_size)

    # gloo = CPU-friendly backend for this local demo. On real GPU nodes,
    # swap to backend="nccl" for multi-GPU, multi-node collective ops.
    dist.init_process_group(backend="gloo")

    torch.manual_seed(0)
    model = nn.Sequential(
        nn.Linear(args.dim, args.dim),
        nn.ReLU(),
        nn.Linear(args.dim, 10),
    )
    ddp_model = nn.parallel.DistributedDataParallel(model)
    optimizer = torch.optim.SGD(ddp_model.parameters(), lr=0.01)
    loss_fn = nn.CrossEntropyLoss()

    print(
        f"[rank {args.rank}/{args.world_size}] process group initialized "
        f"(master={args.master_addr}:{args.master_port})",
        flush=True,
    )

    for step in range(args.steps):
        start = time.perf_counter()

        x = torch.randn(args.batch_size, args.dim)
        y = torch.randint(0, 10, (args.batch_size,))

        optimizer.zero_grad()
        out = ddp_model(x)
        loss = loss_fn(out, y)
        loss.backward()  # gradients all-reduced across nodes here
        optimizer.step()

        elapsed = time.perf_counter() - start
        throughput = args.batch_size / elapsed

        if step % 10 == 0 or step == args.steps - 1:
            print(
                f"[rank {args.rank}] step={step:03d} loss={loss.item():.4f} "
                f"throughput={throughput:.1f} samples/sec step_time={elapsed * 1000:.1f}ms",
                flush=True,
            )

    dist.destroy_process_group()
    print(f"[rank {args.rank}] training complete", flush=True)


if __name__ == "__main__":
    main()
