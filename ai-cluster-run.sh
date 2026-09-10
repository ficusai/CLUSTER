#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${APP_DIR}/.run.log"
PID_FILE="${APP_DIR}/.run.pid"
APP_PID_FILE="${PID_FILE}"

mkdir -p "$(dirname "${LOG_FILE}")" 2>/dev/null || true
export CLUSTER_LAUNCH_START="$(date '+%Y-%m-%d %H:%M:%S')"

log() {
    local msg="$1"
    local level="${2:-INFO}"
    local ts
    ts="$(date '+%H:%M:%S')"
    echo "[ai-cluster ${ts}] [${level}] ${msg}"
    echo "[ai-cluster ${ts}] [${level}] ${msg}" >> "${LOG_FILE}"
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

_shell_init() {
    set +u
    [ -f /etc/profile ] && . /etc/profile || true
    [ -f "${HOME}/.profile" ] && . "${HOME}/.profile" || true
    [ -f "${HOME}/.bash_profile" ] && . "${HOME}/.bash_profile" || true
    [ -n "${BASH_VERSION:-}" ] && [ -f "${HOME}/.bashrc" ] && . "${HOME}/.bashrc" || true
    set -u
    export PATH="${HOME}/.cargo/bin:${HOME}/.local/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:${PATH}"
}

_shell_init

check_cmd() {
    command -v "$1" >/dev/null 2>&1
}

log_success "=== Launch started at ${CLUSTER_LAUNCH_START} ==="
log "APP_DIR=${APP_DIR}"
log "USER=${USER:-$(whoami)}"
log "HOME=${HOME}"
log "PATH=${PATH}"

is_running() {
    if [ -f "${PID_FILE}" ]; then
        local pid=""
        pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
        if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
            return 0
        fi
    fi
    if pgrep -f "${APP_DIR}/cluster-supervisor.sh" >/dev/null 2>&1; then
        return 0
    fi
    if pgrep -f "${APP_DIR}/ai-cluster-desktop-root.sh" >/dev/null 2>&1; then
        return 0
    fi
    if pgrep -f "${APP_DIR}/quick-start-cluster.sh" >/dev/null 2>&1; then
        return 0
    fi
    if pgrep -f "python3 .*cluster\.py --root" >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

if is_running; then
    log_failed "cluster is already running"
    echo "cluster is already running. Stop it first with: ${APP_DIR}/ai-cluster-stop.sh"
    send_notify "AI Cluster" "Launch failed: already running"
    read -p "Press Enter to close..." _ || true
    exit 1
fi

cd "${APP_DIR}"

echo $$ > "${PID_FILE}"
log_success "Reserved PID file ${PID_FILE}"

log "Starting cluster (src=${APP_DIR})..."
log "  Kill switch: ${APP_DIR}/ai-cluster-stop.sh"

log "Exec: ${APP_DIR}/quick-start-cluster.sh"

cleanup() {
    log "Shell exiting; cleaning up."
    if [ -f "${APP_PID_FILE}" ]; then
        wrapper_pid="$(cat "${APP_PID_FILE}" 2>/dev/null || true)"
        if [ -n "${wrapper_pid}" ] && kill -0 "${wrapper_pid}" 2>/dev/null; then
            kill -9 "${wrapper_pid}" 2>/dev/null || true
        fi
        rm -f "${APP_PID_FILE}"
    fi
    send_notify "AI Cluster" "Launcher exited"
}
trap cleanup EXIT HUP TERM INT

if "${APP_DIR}/quick-start-cluster.sh"; then
    log_success "quick-start-cluster.sh completed"
else
    rc=$?
    log_failed "quick-start-cluster.sh exited with code ${rc}"
    send_notify "AI Cluster" "Launch failed (code ${rc})"
    read -p "Press Enter to close..." _ || true
    exit ${rc}
fi

read -p "Press Enter to close..." _ || true
exit 0
