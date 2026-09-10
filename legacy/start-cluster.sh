#!/usr/bin/env bash
# =============================================================================
# One-command cluster start
# Usage:
#   ./start-cluster.sh                    # Normal start
#   ./start-cluster.sh --with-android     # Also start Android worker via SSH
#   ./start-cluster.sh --supervisor       # Use auto-healing supervisor
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_IP="${ROOT_IP:-127.0.0.1}"
RPC_PORT="${RPC_PORT:-50052}"
MODEL_PATH="${MODEL_PATH:-}"

echo "============================================"
echo "  AI Cluster — One-Click Start"
echo "  Root: ${ROOT_IP}"
echo "  Model: ${MODEL_PATH}"
echo "============================================"

log() {
    local msg="$1"
    local level="${2:-INFO}"
    local ts
    ts="$(date '+%H:%M:%S')"
    echo "[start ${ts}] [${level}] ${msg}"
}

log_success() { log "$1" "SUCCESS"; }
log_failed()  { log "$1 FAILED" "ERROR"; }

send_notify() {
    local title="$1"
    local body="$2"
    if command -v notify-send >/dev/null 2>&1; then
        notify-send -u normal -t 6000 "${title}" "${body}" || true
    fi
}

log "Starting cluster sequence..."

# Kill any existing cluster processes
log "Stopping any existing cluster processes..."
pkill -f "llama-server" 2>/dev/null || true
pkill -f "rpc-server" 2>/dev/null || true
sleep 1
log_success "Cluster processes stopped"

# Start Android worker if requested
# NOTE: This is a legacy path. The current launcher (launcher.sh) uses inline SSH commands.
# Android SSH-onboarding is deprecated; kept for backward compatibility only.
if [ "${1:-}" = "--with-android" ]; then
    if [ -x "${SCRIPT_DIR}/ssh-android.sh" ]; then
        log "Starting Android worker via SSH... (legacy path)"
        "${SCRIPT_DIR}/ssh-android.sh" "pkill -f rpc-server 2>/dev/null; nohup ~/ai-cluster/rpc-server -H 0.0.0.0 -p ${RPC_PORT} -t 8 -c > ~/ai-cluster/rpc.log 2>&1 &" &
        sleep 3
        log_success "Android worker SSH started"
    else
        log "ssh-android.sh not found — Android worker not started."
    fi
fi

# Start cluster
if [ "${1:-}" = "--supervisor" ] || [ "${2:-}" = "--supervisor" ]; then
    log "Starting cluster supervisor (auto-healing)..."
    nohup "${SCRIPT_DIR}/cluster-supervisor.sh" &>/dev/null &
    SUPERVISOR_PID=$!
    log_success "Supervisor started (PID: ${SUPERVISOR_PID})"
else
    log "Starting root node..."
    nohup "${SCRIPT_DIR}/start-root.sh" &>/dev/null &
    ROOT_PID=$!
    log_success "Root started (PID: ${ROOT_PID})"
fi

sleep 5
log "Testing API..."
if curl -s http://${ROOT_IP}:8080/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"messages":[{"role":"user","content":"Hi"}],"max_tokens":5}' \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅', d['choices'][0]['message']['content'])" 2>/dev/null; then
    log_success "API test passed"
else
    log "Server still loading (wait 15s and retry)"
    send_notify "AI Cluster" "Server still loading"
fi

echo ""
echo "  API:  http://${ROOT_IP}:8080/v1/chat/completions"
echo "  WEB:  http://${ROOT_IP}:8080"
echo "  Logs: ${SCRIPT_DIR}/cluster.log"
send_notify "AI Cluster" "Cluster started"
