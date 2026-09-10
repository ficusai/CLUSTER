#!/usr/bin/env bash
# Deploy cluster-worker to a remote device via SSH
# Usage: ./deploy-worker.sh <user@host> [--port PORT] [--ai-mode]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_DIR/dist"
CONFIG="$PROJECT_DIR/config.yaml"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <user@host> [--port PORT] [--ai-mode]"
    echo "       $0 --auto              # auto-discover and deploy"
    echo ""
    echo "Examples:"
    echo "  $0 user@192.168.1.100"
    echo "  $0 user@192.168.1.101:8022 --ai-mode"
    echo "  $0 root@192.168.1.102 --ai-mode"
    echo "  $0 --auto                   # scan mDNS + UDP for workers"
    exit 1
fi

SSH_OPTS=(
    -o StrictHostKeyChecking=no
    -o UserKnownHostsFile=/dev/null
    -o ServerAliveInterval=15
    -o ServerAliveCountMax=3
    -o TCPKeepAlive=yes
)

# Find worker binary
WORKER_BIN=""
for f in "$DIST_DIR"/cluster-*; do
    if [ -f "$f" ] && [ -x "$f" ]; then
        WORKER_BIN="$f"
        break
    fi
done

if [ -z "$WORKER_BIN" ]; then
    echo "No built worker binary found in $DIST_DIR"
    echo "Run ./build/build.sh first."
    exit 1
fi

TARGET="$1"
EXTRA_ARGS=""
shift

while [ $# -gt 0 ]; do
    case "$1" in
        --ai-mode) EXTRA_ARGS="$EXTRA_ARGS --ai-mode" ;;
        --port) EXTRA_ARGS="$EXTRA_ARGS --port $2"; shift ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
    shift
done

echo "=== Deploying worker to $TARGET ==="
echo "Binary: $WORKER_BIN"

# Parse host and port
HOST="${TARGET%:*}"
PORT="${TARGET#*:}"
if [ "$HOST" = "$PORT" ]; then
    PORT=22
fi

REMOTE_PATH="~/cluster-worker"

# SCP the binary
echo "→ Copying binary..."
scp "${SSH_OPTS[@]}" -P "$PORT" "$WORKER_BIN" "${HOST}:${REMOTE_PATH}" 2>&1

# Make executable and run
echo "→ Starting worker..."
ssh "${SSH_OPTS[@]}" -p "$PORT" "$HOST" \
    "chmod +x ${REMOTE_PATH} && nohup ${REMOTE_PATH} ${EXTRA_ARGS} > ~/cluster-worker.log 2>&1 &"

echo "→ Worker deployed! Check ~/cluster-worker.log on the target."
echo "→ Logs: ssh ${SSH_OPTS[*]} -p $PORT $HOST 'tail -f ~/cluster-worker.log'"
