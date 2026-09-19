#!/usr/bin/env bash
# =============================================================================
# AI Cluster Supervisor — Keeps the cluster alive with auto-healing
#
# What it does:
#   1. Starts local rpc-server (this machine as a worker)
#   2. Monitors all known workers via TCP port checks every 15 seconds
#   3. When workers join/leave, rebuilds RPC topology and restarts llama-server
#   4. Recovers from crashes automatically
#
# Usage:
#   ./cluster-supervisor.sh              # Run in foreground
#   nohup ./cluster-supervisor.sh &       # Run in background
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/cluster-config.env"

BIN_DIR="${SCRIPT_DIR}/../bin"
LOG_FILE="${SCRIPT_DIR}/cluster.log"

LD_LIBRARY_PATH="${BIN_DIR}:${LD_LIBRARY_PATH:-}"
export LD_LIBRARY_PATH

CHECK_INTERVAL=15
RPC_PORT="${RPC_PORT:-50052}"

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${2:-INFO}] $*" | tee -a "${LOG_FILE}"; }
log_success() { log "$1" "SUCCESS"; }
log_failed()  { log "$1 FAILED" "ERROR"; }

send_notify() {
    local title="$1"
    local body="$2"
    if command -v notify-send >/dev/null 2>&1; then
        notify-send -u normal -t 6000 "${title}" "${body}" || true
    fi
}

check_port() {
    timeout 3 bash -c "echo >/dev/tcp/$1/$2" 2>/dev/null
}

cleanup() {
    log "Supervisor stopping..."
    kill $LOCAL_RPC_PID 2>/dev/null || true
    kill $SERVER_PID 2>/dev/null || true
    log_success "Supervisor stopped."
    send_notify "AI Cluster" "Supervisor stopped"
}
trap cleanup EXIT INT TERM

# Resolve model path
MODEL_PATH="${MODEL_PATH:-../models/qwen2.5-1.5b-instruct-q4_k_m.gguf}"
[[ "${MODEL_PATH}" != /* ]] && MODEL_PATH="${SCRIPT_DIR}/${MODEL_PATH}"

# Worker definitions: "LABEL|IP:PORT"
WORKERS=(
    "Worker1-antiX|${WORKER1_IP}:${RPC_PORT}"
    "Worker2-iPhone|${WORKER2_IP}:${RPC_PORT}"
    "Worker3-Android|${WORKER3_IP}:${RPC_PORT}"
)

start_local_rpc() {
    log "Starting local RPC server on port ${RPC_PORT}..."
    if [ ! -x "${BIN_DIR}/rpc-server" ]; then
        log_failed "rpc-server binary not found or not executable at ${BIN_DIR}/rpc-server"
        return 1
    fi
    "${BIN_DIR}/rpc-server" -H 0.0.0.0 -p "${RPC_PORT}" -t "$(nproc)" &
    LOCAL_RPC_PID=$!
    sleep 1
    if kill -0 "${LOCAL_RPC_PID}" 2>/dev/null; then
        log_success "Local RPC server started (PID: ${LOCAL_RPC_PID})"
    else
        log_failed "Local RPC server failed to start"
        return 1
    fi
}

get_active_endpoints() {
    local eps="127.0.0.1:${RPC_PORT}"
    for worker in "${WORKERS[@]}"; do
        local label="${worker%%|*}"
        local ip_port="${worker#*|}"
        local ip="${ip_port%:*}"
        local port="${ip_port#*:}"
        if check_port "$ip" "$port"; then
            eps="${eps},${ip}:${port}"
        else
            log "Worker ${label} at ${ip}:${port} unreachable"
        fi
    done
    echo "$eps"
}

start_server() {
    local endpoints="$1"
    if [ ! -f "${MODEL_PATH}" ]; then
        log_failed "Cannot start server: model not found at ${MODEL_PATH}"
        send_notify "AI Cluster" "llama-server failed: model not found"
        return 1
    fi
    log "Starting llama-server with endpoints: ${endpoints}"
    if [ ! -x "${BIN_DIR}/llama-server" ]; then
        log_failed "llama-server binary not found at ${BIN_DIR}/llama-server"
        return 1
    fi
    "${BIN_DIR}/llama-server" -m "${MODEL_PATH}" --host 0.0.0.0 --port 8080 \
        -ngl "${N_GPU_LAYERS:-0}" --rpc "${endpoints}" -c 4096 --no-mmap &
    SERVER_PID=$!
    sleep 2
    if kill -0 "${SERVER_PID}" 2>/dev/null; then
        log_success "llama-server started (PID: ${SERVER_PID})"
        log "API: http://${ROOT_IP}:8080/v1/chat/completions"
    else
        log_failed "llama-server failed to start"
        return 1
    fi
}

get_worker_status() {
    local status=""
    for worker in "${WORKERS[@]}"; do
        local ip_port="${worker#*|}"
        local ip="${ip_port%:*}"
        local port="${ip_port#*:}"
        if check_port "$ip" "$port"; then
            status="${status}1"
        else
            status="${status}0"
        fi
    done
    echo "$status"
}

# Main
log "============================================"
log "  AI Cluster Supervisor v2"
log "  Checking workers every ${CHECK_INTERVAL}s"
log_success "Supervisor initializing..."
log "  Log: ${LOG_FILE}"
log "============================================"

if start_local_rpc; then
    log_success "Local RPC initialization complete"
else
    log_failed "Local RPC initialization failed"
    send_notify "AI Cluster" "Supervisor failed to start RPC"
    exit 1
fi

CURRENT_ENDPOINTS=$(get_active_endpoints)
if start_server "$CURRENT_ENDPOINTS"; then
    log_success "llama-server initialization complete"
else
    log_failed "llama-server initialization failed"
    exit 1
fi

LAST_STATUS=""
set +e
while true; do
    sleep "${CHECK_INTERVAL}"

    # Crash recovery
    if ! kill -0 "$LOCAL_RPC_PID" 2>/dev/null; then
        log "Local RPC server crashed! Restarting..."
        start_local_rpc
        CURRENT_ENDPOINTS=$(get_active_endpoints)
        kill $SERVER_PID 2>/dev/null; wait $SERVER_PID 2>/dev/null
        sleep 1
        if ! start_server "$CURRENT_ENDPOINTS"; then
            log_failed "Failed to restart llama-server after RPC crash"
        fi
        continue
    fi

    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        log "llama-server crashed! Restarting..."
        CURRENT_ENDPOINTS=$(get_active_endpoints)
        if ! start_server "$CURRENT_ENDPOINTS"; then
            log_failed "Failed to restart llama-server"
        fi
        continue
    fi

    # Topology check
    NEW_STATUS=$(get_worker_status)
    [ "$NEW_STATUS" = "$LAST_STATUS" ] && continue
    LAST_STATUS="$NEW_STATUS"

    local_status=""
    for i in "${!WORKERS[@]}"; do
        label="${WORKERS[$i]%%|*}"
        state="${NEW_STATUS:$i:1}"
        if [ "$state" = "1" ]; then
            local_status="${local_status} ✅${label}"
        else
            local_status="${local_status} ❌${label}"
        fi
    done
    log "Topology changed:${local_status}"

    NEW_ENDPOINTS=$(get_active_endpoints)
    if [ "$NEW_ENDPOINTS" != "$CURRENT_ENDPOINTS" ]; then
        log "Rebuilding RPC topology..."
        kill $SERVER_PID 2>/dev/null; wait $SERVER_PID 2>/dev/null
        sleep 1
        if ! start_server "$NEW_ENDPOINTS"; then
            log_failed "Failed to rebuild RPC topology"
        fi
        CURRENT_ENDPOINTS="$NEW_ENDPOINTS"
    fi
done
