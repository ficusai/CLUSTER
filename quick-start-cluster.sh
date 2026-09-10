#!/usr/bin/env bash
# Quick-start the AI cluster auto-connect system
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
CLUSTER_BIN=""
LOG_FILE="${SCRIPT_DIR}/.run.log"

mkdir -p "$(dirname "${LOG_FILE}")" 2>/dev/null || true

log() {
    local msg="$1"
    local level="${2:-INFO}"
    local ts
    ts="$(date '+%H:%M:%S')"
    echo "[quick-start ${ts}] [${level}] ${msg}"
    echo "[quick-start ${ts}] [${level}] ${msg}" >> "${LOG_FILE}"
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

# Try to find the binary
for candidate in "$SCRIPT_DIR/dist/cluster-${PLATFORM}-${ARCH}" \
                 "$SCRIPT_DIR"/dist/cluster-*; do
    [ -f "$candidate" ] && [ -x "$candidate" ] && { CLUSTER_BIN="$candidate"; break; }
done

# Fallback: run as Python script
if [ -z "$CLUSTER_BIN" ]; then
    if [ -f "$SCRIPT_DIR/cluster.py" ]; then
        CLUSTER_BIN="python3 $SCRIPT_DIR/cluster.py"
    else
        log_failed "No binary or cluster.py found in $SCRIPT_DIR"
        send_notify "AI Cluster" "Quick-start failed: no binary found"
        echo "Error: No binary or cluster.py found in $SCRIPT_DIR"
        echo "Build first: cd $SCRIPT_DIR && ./build/build.sh"
        exit 1
    fi
fi

echo "╔══════════════════════════════════════════════════╗"
echo "║   AI Cluster Auto-Connect — Quick Start          ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Binary: $CLUSTER_BIN"
echo ""
echo "Modes:"
echo "  1) Start ROOT (coordinator)"
echo "  2) Start WORKER (auto-connect to root)"
echo "  3) Start local test (root + worker on this device)"
echo ""

read -p "Choose mode [1-3]: " mode

case "$mode" in
    1)
        echo "Starting ROOT..."
        if $CLUSTER_BIN --root; then
            log_success "ROOT mode exited cleanly"
        else
            rc=$?
            log_failed "ROOT mode exited with code ${rc}"
            send_notify "AI Cluster" "ROOT mode failed (code ${rc})"
            exit ${rc}
        fi
        ;;
    2)
        read -p "Root IP (leave blank for auto-discovery): " root_ip
        if [ -n "$root_ip" ]; then
            if $CLUSTER_BIN --worker --root-ip "$root_ip"; then
                log_success "WORKER mode exited cleanly"
            else
                rc=$?
                log_failed "WORKER mode exited with code ${rc}"
                send_notify "AI Cluster" "WORKER mode failed (code ${rc})"
                exit ${rc}
            fi
        else
            if $CLUSTER_BIN --worker; then
                log_success "WORKER mode exited cleanly"
            else
                rc=$?
                log_failed "WORKER mode exited with code ${rc}"
                send_notify "AI Cluster" "WORKER mode failed (code ${rc})"
                exit ${rc}
            fi
        fi
        ;;
    3)
        echo "Starting local test (root + worker)..."
        log "Starting local test (root + worker)..."
        $CLUSTER_BIN --root --ctrl-port 52057 --http-port 8083 &
        ROOT_PID=$!
        log "Launched ROOT PID=${ROOT_PID}"
        sleep 2
        if ! kill -0 "${ROOT_PID}" 2>/dev/null; then
            log_failed "ROOT process died immediately"
            send_notify "AI Cluster" "Local test: ROOT died immediately"
            exit 1
        fi
        $CLUSTER_BIN --worker --root-ip 127.0.0.1 --ctrl-port 52057 &
        WORKER_PID=$!
        log "Launched WORKER PID=${WORKER_PID}"
        sleep 2
        if ! kill -0 "${WORKER_PID}" 2>/dev/null; then
            log_failed "WORKER process died immediately"
            send_notify "AI Cluster" "Local test: WORKER died immediately"
            kill "${ROOT_PID}" 2>/dev/null || true
            exit 1
        fi
        log_success "Local test running (ROOT=${ROOT_PID} WORKER=${WORKER_PID})"
        echo "ROOT PID: $ROOT_PID, WORKER PID: $WORKER_PID"
        echo "API: http://localhost:8083/api/status"
        echo "Press Enter to stop..."
        read -r
        kill "${ROOT_PID}" "${WORKER_PID}" 2>/dev/null || true
        wait 2>/dev/null || true
        log_success "Local test stopped"
        echo "Stopped."
        ;;
    *)
        log_failed "Invalid choice: ${mode}"
        send_notify "AI Cluster" "Invalid mode selection"
        echo "Invalid choice."
        exit 1
        ;;
esac
