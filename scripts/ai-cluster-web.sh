#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${APP_DIR}/runtime/.run.log"

mkdir -p "$(dirname "${LOG_FILE}")" 2>/dev/null || true

log() {
    local msg="$1"
    local level="${2:-INFO}"
    local ts
    ts="$(date '+%H:%M:%S')"
    echo "[web ${ts}] [${level}] ${msg}"
    echo "[web ${ts}] [${level}] ${msg}" >> "${LOG_FILE}"
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

log "Opening web dashboard..."

# Open web dashboard in default browser after a short delay
if (sleep 3 && xdg-open "http://localhost:8080") >/dev/null 2>&1; then
    log_success "Web dashboard URL opened"
else
    log "Browser open failed, dashboard available at http://localhost:8080"
fi

echo "Starting AI Cluster with web dashboard..."
echo "Dashboard will open at http://localhost:8080"
echo ""

if python3 "${APP_DIR}/cluster.py" --root "$@"; then
    log_success "Root cluster exited cleanly"
else
    rc=$?
    log_failed "Root cluster exited with code ${rc}"
    send_notify "AI Cluster" "Web cluster exited (code ${rc})"
    exit ${rc}
fi
