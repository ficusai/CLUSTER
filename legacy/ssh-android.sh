#!/usr/bin/env bash
# SSH to Android worker with keepalive to prevent disconnects
# Usage:
#   ./ssh-android.sh <command>          # Run a command
#   ./ssh-android.sh --persist          # Keep reconnecting (for long-lived sessions)

SSH_OPTS=(
    -i "$(dirname "$0")/android_ssh_key"
    -o StrictHostKeyChecking=no
    -o UserKnownHostsFile=/dev/null
    -o ServerAliveInterval=15
    -o ServerAliveCountMax=3
    -o TCPKeepAlive=yes
    -p 8022
    u0_a377@10.0.0.108
)

if [ "${1:-}" = "--persist" ]; then
    shift
    CMD="${*:-~/ai-cluster/start-worker.sh}"
    echo "[SSH] Persistent mode. Auto-reconnecting on disconnect..."
    while true; do
        ssh "${SSH_OPTS[@]}" "$CMD" || true
        echo "[SSH] Disconnected at $(date). Reconnecting in 5s..."
        sleep 5
    done
else
    exec ssh "${SSH_OPTS[@]}" "$@"
fi
