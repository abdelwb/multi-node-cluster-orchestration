# Single image used for both the controller and compute nodes; the
# entrypoint decides which daemon to run based on the ROLE env var set in
# docker-compose.yml. This mirrors how real clusters are often built from
# one base OS image with role-specific config/services layered on top.

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# The munge/slurmd/slurmctld .deb packages' postinst scripts try to start
# their daemons via the init system on install. There's no init system at
# build time inside Docker, which otherwise makes apt-get install fail; this
# policy-rc.d stub tells any postinst "don't start services now" (we start
# them ourselves from entrypoint.sh at container runtime instead).
RUN printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d \
    && chmod +x /usr/sbin/policy-rc.d

RUN apt-get update && apt-get install -y --no-install-recommends \
        slurmd slurmctld munge libmunge2 \
        python3 python3-pip \
        iproute2 iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# CPU build of PyTorch - enough to run the demo DDP job. On a real GPU
# cluster this training job instead runs inside an NVIDIA NGC PyTorch
# container (nvcr.io/nvidia/pytorch) via Pyxis/Enroot; see
# jobs/submit_distributed_training.sbatch.
RUN pip3 install --no-cache-dir numpy torch --index-url https://download.pytorch.org/whl/cpu

# Slurm's packaged default config directory differs across distro versions
# (/etc/slurm-llnl vs /etc/slurm). Rather than depend on that, install our
# config at a fixed path and point Slurm at it explicitly via SLURM_CONF,
# which every Slurm daemon/command honors regardless of build-time default.
RUN mkdir -p /etc/slurm
COPY config/slurm.conf /etc/slurm/slurm.conf
COPY config/gres.conf /etc/slurm/gres.conf
COPY config/cgroup.conf /etc/slurm/cgroup.conf
ENV SLURM_CONF=/etc/slurm/slurm.conf

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
    && mkdir -p /var/spool/slurmctld /var/spool/slurmd /var/log/slurm /home/demo/jobs/logs \
    && chown -R slurm:slurm /var/spool/slurmctld /var/spool/slurmd /var/log/slurm

ENTRYPOINT ["/entrypoint.sh"]
