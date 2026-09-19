#!/usr/bin/env bash
# =============================================================================
# Start the ROOT node (MacBook Pro A1502 - Fedora)
# Launches local RPC + llama-server, discovers available workers.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/cluster-config.env"

BIN_DIR="${SCRIPT_DIR}/../bin"
LD_LIBRARY_PATH="${BIN_DIR}:${LD_LIBRARY_PATH:-}"
export LD_LIBRARY_PATH

LOG_FILE="${SCRIPT_DIR}/cluster.log"
WORKER_TIMEOUT=3
RPC_PORT="${RPC_PORT:-50052}"

log()  { echo "[$(date '+%H:%M:%S')] $*" | tee -a "${LOG_FILE}"; }

cleanup() {
    log "[ROOT] Shutting down cluster..."
    kill $LOCAL_RPC_PID 2>/dev/null || true
    kill $SERVER_PID 2>/dev/null || true
    wait 2>/dev/null
    log "[ROOT] All processes stopped."
}
trap cleanup EXIT INT TERM

# TCP port check (more reliable than ping)
check_port() {
    timeout "$WORKER_TIMEOUT" bash -c "echo >/dev/tcp/$1/$2" 2>/dev/null
}

log "============================================"
log "  AI Cluster - Root Node (Fedora)"
log "  Model: ${MODEL_PATH}"
log "============================================"

# 1. Start local RPC server
log "[ROOT] Starting local RPC server on port ${RPC_PORT}..."
"${BIN_DIR}/rpc-server" \
    -H 0.0.0.0 \
    -p "${RPC_PORT}" \
    -t "$(nproc)" &
LOCAL_RPC_PID=$!
sleep 1

# 2. Discover available workers (parallel TCP checks)
declare -A WORKERS
WORKERS["Worker1-antiX"]="${WORKER1_IP}:${RPC_PORT}"
WORKERS["Worker2-iPhone"]="${WORKER2_IP}:${RPC_PORT}"
WORKERS["Worker3-Android"]="${WORKER3_IP}:${RPC_PORT}"

RPC_ENDPOINTS="127.0.0.1:${RPC_PORT}"
FOUND=0

log "[ROOT] Discovering workers..."
for name in "${!WORKERS[@]}"; do
    ip_port="${WORKERS[$name]}"
    ip="${ip_port%:*}"
    port="${ip_port#*:}"

    if check_port "$ip" "$port"; then
        log "[ROOT] ✅ ${name} (${ip}:${port}) — connected"
        RPC_ENDPOINTS="${RPC_ENDPOINTS},${ip}:${port}"
        ((FOUND++))
    else
        log "[ROOT] ⚠️  ${name} (${ip}:${port}) — not reachable, skipping"
    fi
done

log "[ROOT] Workers found: ${FOUND}"
log "[ROOT] RPC endpoints: ${RPC_ENDPOINTS}"

# 3. Resolve model path
if [[ "${MODEL_PATH}" != /* ]]; then
    MODEL_PATH="${SCRIPT_DIR}/${MODEL_PATH}"
fi

if [ ! -f "${MODEL_PATH}" ]; then
    log "[ROOT] ERROR: Model not found at ${MODEL_PATH}"
    exit 1
fi

# 4. Start llama-server
log "[ROOT] Starting llama-server..."
log "  API: http://${ROOT_IP}:8080/v1/chat/completions"
log "  WEB: http://${ROOT_IP}:8080"

"${BIN_DIR}/llama-server" \
    -m "${MODEL_PATH}" \
    --host 0.0.0.0 \
    --port 8080 \
    -ngl "${N_GPU_LAYERS}" \
    --rpc "${RPC_ENDPOINTS}" \
    -c 4096 \
    --no-mmap &
SERVER_PID=$!

log ""
log "============================================"
log "  Cluster is LIVE!"
log "  API:  http://${ROOT_IP}:8080/v1/chat/completions"
log "============================================"

wait "$SERVER_PID"
