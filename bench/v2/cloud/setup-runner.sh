#!/bin/bash
# Turn a fresh Ubuntu 24.04 machine (e.g. a rented Hetzner CCX43: 16 vCPU, 64 GB RAM) into an
# ephemeral self-hosted GitHub Actions runner for the manual benchmark workflow
# (.github/workflows/bench.yml). Paste the whole file, with the token filled in, as the
# server's "Cloud config" / user data; or run it as root over SSH:
#   RUNNER_TOKEN=... bash setup-runner.sh
# The token comes from the repository: Settings -> Actions -> Runners -> New self-hosted runner
# (the --token value; it expires after about an hour). The runner is ephemeral: it takes one
# job and then unregisters itself, so a forgotten machine cannot pick up other work. Delete the
# machine afterwards: a stopped server is still billed.
set -euo pipefail
# Keep a log on the machine (cloud-init's own log is in /var/log/cloud-init-output.log too).
exec > >(tee -a /var/log/bench-setup.log) 2>&1
RUNNER_TOKEN=${RUNNER_TOKEN:-PASTE_TOKEN_HERE}
REPO_URL=${REPO_URL:-https://github.com/Matdata-eu/tripletrail-bench}
LABELS=${LABELS:-bench-64g}

export DEBIAN_FRONTEND=noninteractive
# No unattended upgrades on a bench machine: Ubuntu's apt-daily-upgrade timer fires around
# 06:00 (plus up to an hour), and needrestart then restarts services, the runner's among
# them; the Europe scale run 42927990120 lost its runner that way at 06:39, 5.5 h in.
systemctl disable --now apt-daily.timer apt-daily-upgrade.timer unattended-upgrades.service 2>/dev/null || true
systemctl kill --kill-whom=all unattended-upgrades.service 2>/dev/null || true
mkdir -p /etc/needrestart/conf.d
echo "\$nrconf{restart} = 'l';" >/etc/needrestart/conf.d/90-bench.conf
for i in 1 2 3; do apt-get update -q && break; sleep 10; done
apt-get install -y -q ca-certificates curl git jq unzip bc time build-essential clang pkg-config \
  python3 python3-pip python3-venv python3-requests python3-yaml python3-psycopg2 openjdk-21-jre-headless docker.io gh \
  postgresql-client osmium-tool
# perf, for run.py's PERF_QUERIES (core #188); best effort, a run without it just has no profile.
apt-get install -y -q "linux-tools-$(uname -r)" linux-tools-common || echo "no perf for kernel $(uname -r)"
echo 1 >/proc/sys/kernel/perf_event_paranoid || true
systemctl enable --now docker

useradd -m -s /bin/bash -G docker gha || true
# The runner's user reads the journal: run_scale.sh streams kills and service stops into the
# run log, the only record left once the server is deleted.
usermod -aG systemd-journal,adm gha || true
# No userspace OOM killer: systemd-oomd kills whole services (the runner's with it) under
# memory pressure, which a bench of a store larger than memory is under by design. The
# kernel's OOM killer still ends a process that runs out of memory, with a line in the log.
systemctl disable --now systemd-oomd.service systemd-oomd.socket 2>/dev/null || true

# The workflow's extra volume (input volume_gb), formatted by Hetzner. Mounted here when Hetzner's
# automount has not done it (the first run waiting for automount never got its runner, #218), at
# /mnt/HC_Volume_<id> as automount would, and linked to /bench-volume for the runner's user. Never
# fatal: without it the runner still comes up and the bench job fails with a clear error.
if [ -n "${VOLUME_ID:-}" ]; then
  vdev=/dev/disk/by-id/scsi-0HC_Volume_$VOLUME_ID vmnt=/mnt/HC_Volume_$VOLUME_ID
  for _ in $(seq 1 60); do [ -e "$vdev" ] && break; sleep 5; done
  if ! mountpoint -q "$vmnt" && [ -e "$vdev" ]; then
    mkdir -p "$vmnt"
    mount -o discard,defaults "$vdev" "$vmnt" || echo "mounting $vdev failed" >&2
  fi
  if mountpoint -q "$vmnt"; then
    chown gha:gha "$vmnt"
    ln -sfn "$vmnt" /bench-volume
    df -h "$vmnt"
  else
    echo "volume $VOLUME_ID is not mounted (device $vdev: $(ls -l "$vdev" 2>&1))" >&2
  fi
fi
# Rust for the tripletrail build (the workflow pins the toolchain itself).
sudo -u gha bash -c 'curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal'

# A pinned runner version: the unauthenticated "latest release" API call is rate-limited per IP,
# and rented servers share IPs, so it can fail and stop this script before the runner exists.
ver=${RUNNER_VERSION:-2.338.2}
sudo -u gha bash -c "mkdir -p ~/runner && cd ~/runner && \
  curl -sSfL -o r.tgz https://github.com/actions/runner/releases/download/v$ver/actions-runner-linux-x64-$ver.tar.gz && \
  tar xzf r.tgz && rm r.tgz && \
  ./config.sh --unattended --ephemeral --url '$REPO_URL' --token '$RUNNER_TOKEN' --labels '$LABELS' --name \$(hostname)"
cd /home/gha/runner && ./svc.sh install gha
# systemd stops a whole service when the kernel's OOM killer ends one of its processes
# (OOMPolicy=stop is the default), so one engine running out of memory took the runner, and the
# rest of the run, with it (run 45816390204). Keep the runner: the engine's job records the kill.
for unit in /etc/systemd/system/actions.runner.*.service; do
  mkdir -p "$unit.d"
  printf '[Service]\nOOMPolicy=continue\n' >"$unit.d/oom.conf"
done
systemctl daemon-reload
./svc.sh start
