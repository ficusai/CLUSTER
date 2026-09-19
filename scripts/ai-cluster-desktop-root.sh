#!/usr/bin/env bash
# Desktop entry wrapper for AI Cluster root mode.
# Runs the root coordinator in the current terminal so the .desktop entry
# with Terminal=true opens exactly one window.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"
mkdir -p "${LOG_DIR}" "${PROJECT_DIR}/runtime" 2>/dev/null || true
LOG_FILE="${LOG_DIR}/desktop-root.log"
LOCK_FILE="${PROJECT_DIR}/runtime/desktop-root.lock"

log() {
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[${ts}] $*" | tee -a "${LOG_FILE}" >/dev/null
    echo "[${ts}] $*"
}

cleanup_lock() {
    rm -f "${LOCK_FILE}" 2>/dev/null || true
}

if [ -f "${LOCK_FILE}" ]; then
    old_pid=$(cat "${LOCK_FILE}" 2>/dev/null || echo "")
    if [ -n "${old_pid}" ] && kill -0 "${old_pid}" 2>/dev/null; then
        echo "AI Cluster root is already running as PID ${old_pid}. Open http://localhost:8080"
        exit 0
    else
        cleanup_lock
    fi
fi

echo $$ > "${LOCK_FILE}"
trap cleanup_lock EXIT

stop_stale() {
    local my_pid=$$
    local my_ppid=${PPID:-}
    local pids
    pids=$(pgrep -f "python3 .*cluster\.py --root" 2>/dev/null || true)
    pids="${pids}$(pgrep -f "${PROJECT_DIR}/dist/cluster-.* --root" 2>/dev/null || true)"
    pids="${pids}$(pgrep -f "${PROJECT_DIR}/scripts/ai-cluster-desktop-root.sh" 2>/dev/null || true)"
    # Exclude this wrapper's own PID and its parent so stop_stale does not
    # kill the currently-running launcher before exec python3.
    pids=$(printf '%s\n' "${pids}" | grep -vE "^${my_pid}$|^${my_ppid}$" || true)
    if [ -n "${pids}" ]; then
        log "Stopping stale root cluster process(es)..."
        echo "${pids}" | xargs -r kill -TERM 2>/dev/null || true
        sleep 2
        pids=$(pgrep -f "python3 .*cluster\.py --root" 2>/dev/null || true)
        pids="${pids}$(pgrep -f "${PROJECT_DIR}/dist/cluster-.* --root" 2>/dev/null || true)"
        if [ -n "${pids}" ]; then
            echo "${pids}" | xargs -r kill -KILL 2>/dev/null || true
            sleep 0.5
        fi
    fi
    # Also kill any stranded auto-onboard / deploy children from prior runs.
    for label in \
        "${PROJECT_DIR}/scripts/ai-cluster-auto-onboard.sh" \
        "ssh -i .*android_ssh_key" \
        "tar -C .*ai-cluster.* -xf" \
        "timeout .*ssh .*ai-cluster" \
        "scp .*ai-cluster"
    do
        local childs
        childs=$(pgrep -f "${label}" 2>/dev/null || true)
        if [ -n "${childs}" ]; then
            log "Killing stranded ${label} process(es)..."
            echo "${childs}" | xargs -r kill -TERM 2>/dev/null || true
            sleep 1
            childs=$(pgrep -f "${label}" 2>/dev/null || true)
            [ -n "${childs}" ] && echo "${childs}" | xargs -r kill -KILL 2>/dev/null || true
        fi
    done
    # Release ports belonging to this project's own processes.
    for port in 52053 50052 8080 8081; do
        local leftover
        leftover=$(lsof -ti tcp:"${port}" -c python3 -c llama-server -c rpc-server 2>/dev/null | sort -u || true)
        [ -n "${leftover}" ] && echo "${leftover}" | xargs -r kill -9 2>/dev/null || true
    done
}

# Open dashboard after the root HTTP server has had time to start.
open_dashboard() {
    local url="http://localhost:8080"
    for _ in $(seq 1 30); do
        if curl -fsS "${url}/api/status" >/dev/null 2>&1; then
            xdg-open "${url}" >/dev/null 2>&1 || true
            return 0
        fi
        sleep 1
    done
    log "Dashboard did not become reachable; browse to ${url} manually."
}

stop_stale
log "Starting AI Cluster root coordinator..."
(sleep 3 && open_dashboard) >/dev/null 2>&1 &
(sleep 6 && "${PROJECT_DIR}/scripts/ai-cluster-auto-onboard.sh" >> "${LOG_DIR}/desktop-root.log" 2>&1) >/dev/null 2>&1 &

cd "${PROJECT_DIR}"
exec python3 "${PROJECT_DIR}/cluster.py" --root --no-ui
