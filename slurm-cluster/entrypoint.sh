#!/bin/bash
# Entrypoint shared by the controller and both compute nodes. ROLE (set in
# docker-compose.yml) picks which Slurm daemon this container runs.
set -euo pipefail

MUNGE_KEY=/etc/munge/munge.key

# /run is a fresh tmpfs in a container - nothing creates munge's runtime
# socket dir the way the systemd unit normally would on a real host.
mkdir -p /run/munge
chown munge:munge /run/munge

# All nodes must share one munge key to authenticate RPCs to each other.
# It's generated once by the controller onto a shared named volume; compute
# nodes wait for it to appear rather than generating their own.
if [ "${ROLE:-}" = "controller" ]; then
    if [ ! -f "$MUNGE_KEY" ]; then
        /usr/sbin/create-munge-key -f
    fi
else
    echo "compute node: waiting for munge key from controller..."
    until [ -f "$MUNGE_KEY" ]; do sleep 1; done
fi

chown munge:munge "$MUNGE_KEY"
chmod 400 "$MUNGE_KEY"

# munged refuses to run as root; drop to the munge user.
runuser -u munge -- /usr/sbin/munged

# Give munge a moment to come up before Slurm tries to authenticate through it.
sleep 2

case "${ROLE:-}" in
    controller)
        echo "starting slurmctld (controller)"
        exec /usr/sbin/slurmctld -D
        ;;
    compute)
        echo "starting slurmd (compute node: ${SLURMD_NODENAME:-$(hostname)})"
        exec /usr/sbin/slurmd -D
        ;;
    *)
        echo "ERROR: ROLE must be 'controller' or 'compute' (got '${ROLE:-unset}')" >&2
        exit 1
        ;;
esac
