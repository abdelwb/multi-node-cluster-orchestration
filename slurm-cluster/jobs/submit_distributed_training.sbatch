#!/bin/bash
#SBATCH --job-name=ddp-train
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --partition=demo
#SBATCH --output=/home/demo/jobs/logs/%x-%j.out

# Multi-node distributed training job: one task per node, rendezvousing
# through the first allocated node. This is the same launch pattern used on
# a real Slurm/DGX cluster - only the container image and backend change.
mkdir -p /home/demo/jobs/logs

export MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n1)
export MASTER_PORT=29500

echo "Launching DDP job across nodes: $SLURM_JOB_NODELIST (master=$MASTER_ADDR:$MASTER_PORT)"

# --- Local CPU demo (default: runs directly on the compute node image) ---
srun --export=ALL bash -c '
    python3 /home/demo/jobs/train_ddp.py \
        --rank="$SLURM_PROCID" \
        --world-size="$SLURM_NTASKS" \
        --master-addr="$MASTER_ADDR" \
        --master-port="$MASTER_PORT"
'

# --- Production path: run the identical job inside an NVIDIA NGC PyTorch
#     container on real GPU nodes, using Pyxis + Enroot (the standard way
#     Slurm launches containerized jobs on NVIDIA DGX / SuperPOD clusters).
#     Swap --backend=gloo for --backend=nccl in train_ddp.py to use GPUs.
#
# srun --container-image=nvcr.io/nvidia/pytorch:24.08-py3 \
#      --container-mounts=/home/demo/jobs:/workspace \
#      --gres=gpu:1 \
#      bash -c '
#          python3 /workspace/train_ddp.py \
#              --rank="$SLURM_PROCID" \
#              --world-size="$SLURM_NTASKS" \
#              --master-addr="$MASTER_ADDR" \
#              --master-port="$MASTER_PORT"
#      '
