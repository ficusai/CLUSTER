#!/usr/bin/env bash
# =============================================================================
# SSH to iPhone via USB (iproxy tunnel) or Wi-Fi
# Usage:
#   ./ssh-iphone.sh                    # Interactive shell via USB
#   ./ssh-iphone.sh <command>          # Run command via USB
#   ./ssh-iphone.sh --wifi <command>   # Run command via Wi-Fi
#   ./ssh-iphone.sh --persist          # Start worker with auto-reconnect
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/cluster-config.env"
[ -f "${CONFIG_FILE}" ] && source "${CONFIG_FILE}"

IPHONE_IP="${WORKER2_IP:-192.168.1.100}"
KEY="${SCRIPT_DIR}/../security/keys/android_ssh_key"
SSH_PORT=2222
IPROXY_PID=""

cleanup() { [ -n "$IPROXY_PID" ] && kill "$IPROXY_PID" 2>/dev/null; }
trap cleanup EXIT

SSH_OPTS_USB=(
    -i "$KEY"
    -o StrictHostKeyChecking=no
    -o UserKnownHostsFile=/dev/null
    -o ServerAliveInterval=15
    -o ServerAliveCountMax=3
    -p "$SSH_PORT"
    root@localhost
)

SSH_OPTS_WIFI=(
    -i "$KEY"
    -o StrictHostKeyChecking=no
    -o UserKnownHostsFile=/dev/null
    -o ServerAliveInterval=15
    -o ServerAliveCountMax=3
    root@${IPHONE_IP}
)

USE_WIFI=false
ARGS=()
for arg in "$@"; do
    if [ "$arg" = "--wifi" ]; then
        USE_WIFI=true
    else
        ARGS+=("$arg")
    fi
done

if [ "$USE_WIFI" = true ]; then
    if [ "${#ARGS[@]}" -eq 0 ]; then
        exec ssh "${SSH_OPTS_WIFI[@]}"
    else
        exec ssh "${SSH_OPTS_WIFI[@]}" "${ARGS[@]}"
    fi
fi

# USB mode: start iproxy if not running
if ! lsof -i :$SSH_PORT >/dev/null 2>&1; then
    iproxy "$SSH_PORT" 22 &
    IPROXY_PID=$!
    sleep 2
fi

if [ "${#ARGS[@]}" -eq 0 ]; then
    exec ssh "${SSH_OPTS_USB[@]}"
elif [ "${ARGS[0]}" = "--persist" ]; then
    shift
    CMD="${*:-cd ~/ai-cluster && ./start-worker.sh}"
    while true; do
        echo "[ssh-iphone] Connecting..."
        ssh "${SSH_OPTS_USB[@]}" "$CMD" || true
        echo "[ssh-iphone] Disconnected, retrying in 5s..."
        sleep 5
    done
else
    exec ssh "${SSH_OPTS_USB[@]}" "${ARGS[@]}"
fi
