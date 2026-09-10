#!/usr/bin/env bash
# =============================================================================
# Start a WORKER node (MacBook Air / Android / iPhone)
# Runs the RPC server that accepts tasks from the root node.
#
# Usage:
#   ./start-worker.sh                     # Auto-detect (reads config)
#   ROOT_IP=10.0.0.103 ./start-worker.sh  # Explicit root IP
#   ./start-worker.sh --root-ip 10.0.0.103
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse --root-ip argument
if [ "${1:-}" = "--root-ip" ] && [ -n "${2:-}" ]; then
    ROOT_IP="$2"
    shift 2
fi

# Try to load config
if [ -f "${SCRIPT_DIR}/cluster-config.env" ]; then
    source "${SCRIPT_DIR}/cluster-config.env"
fi

# Platform detection
if command -v sysctl &>/dev/null && sysctl -n hw.ncpu &>/dev/null 2>&1; then
    THREADS="$(sysctl -n hw.ncpu 2>/dev/null || echo 4)"
    echo "[WORKER] Platform: iOS/macOS"
elif command -v nproc &>/dev/null; then
    THREADS="$(nproc 2>/dev/null || echo 4)"
    echo "[WORKER] Platform: Linux/Android"
else
    THREADS="4"
    echo "[WORKER] Platform: Unknown"
fi

# Locate rpc-server binary
RPC_BIN=""
for candidate in \
    "${SCRIPT_DIR}/bin/rpc-server" \
    "${SCRIPT_DIR}/rpc-server" \
    "${HOME}/ai-cluster/rpc-server"; do
    if [ -f "${candidate}" ]; then
        RPC_BIN="${candidate}"
        chmod +x "${RPC_BIN}" 2>/dev/null || true
        break
    fi
done

if [ -z "${RPC_BIN}" ]; then
    echo "[WORKER] ERROR: rpc-server binary not found."
    echo "  Looked in: ./bin/rpc-server, ./rpc-server, ~/ai-cluster/rpc-server"
    exit 1
fi

# Root IP: env var -> config -> hardcoded fallback (no prompt)
ROOT_IP="${ROOT_IP:-}"
if [ -z "${ROOT_IP}" ]; then
    ROOT_IP="${ROOT_IP:-}"
fi
if [ -z "${ROOT_IP}" ]; then
    echo "[WORKER] ERROR: ROOT_IP not set. Pass via --root-ip or ROOT_IP env var."
    exit 1
fi

RPC_PORT="${RPC_PORT:-50052}"

cleanup() {
    echo "[WORKER] Shutting down..."
    kill $RPC_PID 2>/dev/null || true
    wait 2>/dev/null
    echo "[WORKER] Stopped."
}
trap cleanup EXIT INT TERM

echo "============================================"
echo "  AI Cluster - Worker Node"
echo "  Binary:  ${RPC_BIN}"
echo "  Root:    ${ROOT_IP}:${RPC_PORT}"
echo "  Threads: ${THREADS}"
echo "============================================"

echo "[WORKER] Starting RPC server on port ${RPC_PORT}..."
"${RPC_BIN}" \
    -H 0.0.0.0 \
    -p "${RPC_PORT}" \
    -t "${THREADS}" \
    -c &
RPC_PID=$!

echo "[WORKER] Worker running. Waiting for tasks from root node..."
echo "[WORKER] Press Ctrl+C to stop."

wait
