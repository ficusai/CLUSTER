#!/usr/bin/env bash
# =============================================================================
# Persistent Android worker connection with auto-reconnect
# Run this in a terminal and it keeps the Android worker connected forever.
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/cluster-config.env"

SSH_KEY="${SCRIPT_DIR}/android_ssh_key"
WORKER_SCRIPT="~/ai-cluster/start-worker.sh"

echo "============================================"
echo "  Android Worker — Persistent Connection"
echo "  Auto-reconnects on disconnect"
echo "  Root IP: ${ROOT_IP}"
echo "============================================"

# Write config to Android (non-interactive)
ssh -i "$SSH_KEY" \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -p 8022 u0_a377@10.0.0.108 \
    "mkdir -p ~/ai-cluster && echo 'ROOT_IP=${ROOT_IP}' > ~/ai-cluster/android-config.env && echo 'RPC_PORT=50052' >> ~/ai-cluster/android-config.env"

# Keep reconnecting
while true; do
    echo "[$(date '+%H:%M:%S')] Connecting Android worker..."
    ssh -i "$SSH_KEY" \
        -o StrictHostKeyChecking=no \
        -o UserKnownHostsFile=/dev/null \
        -o ServerAliveInterval=15 \
        -o ServerAliveCountMax=3 \
        -o TCPKeepAlive=yes \
        -p 8022 u0_a377@10.0.0.108 \
        "ROOT_IP=${ROOT_IP} ${WORKER_SCRIPT}" || true
    echo "[$(date '+%H:%M:%S')] Disconnected. Reconnecting in 5s..."
    sleep 5
done
