#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${APP_DIR}/logs"
PID_FILE="${APP_DIR}/.run.pid"
mkdir -p "${LOG_DIR}"

SESSION_LOG="${LOG_DIR}/session-$(date '+%Y-%m-%d-%H-%M-%S').log"
BASH_LOG="${LOG_DIR}/events.log"
MASTER_LOG="${LOG_DIR}/current.log"

# Bash-side logger
bash_log() {
    local msg="$1"
    local level="${2:-INFO}"
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[events ${ts}] [${level}] ${msg}" | tee -a "${BASH_LOG}" "${MASTER_LOG}"
}

bash_log_success() { bash_log "$1" "SUCCESS"; }
bash_log_failed()  { bash_log "$1 FAILED" "ERROR"; }

send_notify() {
    local title="$1"
    local body="$2"
    if command -v notify-send >/dev/null 2>&1; then
        notify-send -u normal -t 6000 "${title}" "${body}" || true
    fi
}

_cleanup_ai_cluster() {
    bash_log "Shell exiting."
    if [ -n "${RUN_PID:-}" ] && kill -0 "${RUN_PID}" 2>/dev/null; then
        bash_log "Terminating cluster PID ${RUN_PID}..."
        kill -TERM "${RUN_PID}" 2>/dev/null || true
        sleep 1
        kill -0 "${RUN_PID}" 2>/dev/null && kill -9 "${RUN_PID}" 2>/dev/null || true
    fi
    if [ -n "${STATUS_PID:-}" ] && kill -0 "${STATUS_PID}" 2>/dev/null; then
        kill "${STATUS_PID}" 2>/dev/null || true
        wait "${STATUS_PID}" 2>/dev/null || true || true
    fi
    rm -f "${PID_FILE}"
    send_notify "AI Cluster" "Session ended."
}
trap _cleanup_ai_cluster EXIT INT TERM HUP

cat <<INTRO
╔══════════════════════════════════════════════════════════╗
║            AI Cluster — Live Events Window             ║
║       All logs / status / dashboard in one window       ║
╚══════════════════════════════════════════════════════════╝
INTRO

export PATH="${HOME}/.cargo/bin:${HOME}/.local/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:${PATH}"
export PYTHONUNBUFFERED=1

bash_log_success "=== Launch started ==="
bash_log "APP_DIR=${APP_DIR}"
bash_log "SESSION_LOG=${SESSION_LOG}"

# Ensure no stale pid at startup
rm -f "${PID_FILE}"

resolve_running_pid() {
    # Order matters: most-specific wrappers first so desktop/launcher PIDs
    # are preferred over raw process-name matches.
    for pattern in \
        "${APP_DIR}/cluster-supervisor.sh" \
        "${APP_DIR}/ai-cluster-desktop-root.sh" \
        "${APP_DIR}/dist/cluster-.* --root" \
        "python3 .*cluster\.py --root" \
        "${APP_DIR}/quick-start-cluster.sh"
    do
        if pgrep -f "${pattern}" >/dev/null 2>&1; then
            pgrep -f "${pattern}" | head -n1 || true
            return 0
        fi
    done
    if [ -f "${PID_FILE}" ]; then
        local pid
        pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
        if [ -n "${pid}" ] && kill -0 "${pid}" 2>/dev/null; then
            echo "${pid}"
            return 0
        fi
        rm -f "${PID_FILE}"
    fi
    return 1
}

print_api_status() {
    local json
    json="$(curl -s http://127.0.0.1:8080/api/status 2>/dev/null || true)"
    if [ -n "${json}" ]; then
        local ts
        ts="$(date '+%H:%M:%S')"
        printf '\033[1;36m[%s] STATUS %s\033[0m\n' "${ts}" "${json}"
    fi
}

RUN_PID="$(resolve_running_pid || true)"

if [ -n "${RUN_PID}" ]; then
    bash_log "Attaching to existing cluster PID ${RUN_PID}"
    echo "Attaching to existing cluster process ${RUN_PID}"
    echo "Process: $(ps -p "${RUN_PID}" -o comm=,args= 2>/dev/null || true)"
    echo "Dashboard: http://127.0.0.1:8080/api/status"
else
    bash_log "No running cluster detected. Starting new cluster..."
    echo "No running cluster detected. Starting new cluster..."

    PLATFORM="$(uname -s | tr '[:upper:]' '[:lower:]')"
    ARCH="$(uname -m)"
    BIN="${APP_DIR}/dist/cluster-${PLATFORM}-${ARCH}"
    if [ ! -x "${BIN}" ]; then
        BIN="python3 ${APP_DIR}/cluster.py"
    fi

    bash_log "Launching: ${BIN} --root"
    echo "Launching: ${BIN} --root"
    rm -f "${PID_FILE}"
    touch "${SESSION_LOG}" "${MASTER_LOG}"

    # Build command array so paths with spaces are handled safely.
    CMD=()
    if [ -x "${BIN}" ]; then
        CMD+=("${BIN}")
    else
        # BIN is "python3 /path/cluster.py" when dist binary is missing.
        read -ra BIN_ARGS <<< "${BIN}"
        CMD+=("${BIN_ARGS[@]}")
    fi
    CMD+=(--root)

    env PATH="${PATH}" HOME="${HOME}" USER="${USER:-$(whoami)}" PYTHONUNBUFFERED=1 \
        "${CMD[@]}" \
        2>&1 | tee -a "${SESSION_LOG}" "${MASTER_LOG}" &
    LAUNCH_PID=$!
    bash_log "Launcher PID=${LAUNCH_PID}"

    sleep 1.5

    if kill -0 "${LAUNCH_PID}" 2>/dev/null; then
        if ps -p "${LAUNCH_PID}" -o args= 2>/dev/null | grep -qE "cluster-.* --root|cluster.py --root"; then
            RUN_PID="${LAUNCH_PID}"
        else
            RUN_PID="$(pgrep -f "${BIN} --root" 2>/dev/null | head -n1 || true)"
        fi
    else
        RUN_PID="$(pgrep -f "${BIN} --root" 2>/dev/null | head -n1 || true)"
    fi
    : "${RUN_PID:=${LAUNCH_PID}}"

    if [ -n "${RUN_PID}" ] && kill -0 "${RUN_PID}" 2>/dev/null; then
        echo "${RUN_PID}" > "${PID_FILE}"
        bash_log_success "Cluster PID=${RUN_PID}"
    else
        bash_log_failed "Could not confirm a live cluster process"
        send_notify "AI Cluster" "Launch failed: process not confirmed"
    fi
    echo "Cluster PID: ${RUN_PID}"
fi

if [ -z "${RUN_PID}" ] || ! kill -0 "${RUN_PID}" 2>/dev/null; then
    echo "WARNING: could not confirm a live cluster process."
    bash_log "WARNING: could not confirm a live cluster process."
fi

send_notify "AI Cluster Launched" "PID ${RUN_PID:-unknown}"

(
    if [ -n "${RUN_PID:-}" ]; then
        print_api_status || true
        while kill -0 "${RUN_PID:-}" 2>/dev/null; do
            sleep 5
            print_api_status || true
        done
    fi
) &
STATUS_PID=$!

echo
echo "── Session log ──"
tail -n 60 "${SESSION_LOG}" 2>/dev/null || true
echo "────────────────"
if [ -d "${LOG_DIR}" ]; then
    echo
    echo "── Dated logs ──"
    ls -lth "${LOG_DIR}"/*.log 2>/dev/null | head -n 5 || true
    echo "────────────────────"
fi
echo

if [ -n "${RUN_PID:-}" ]; then
    tail -f \
        "${MASTER_LOG}" \
        "${SESSION_LOG}" \
        "${LOG_DIR}"/*.log 2>/dev/null &
    TAIL_PID=$!
    while [ -n "${RUN_PID:-}" ] && kill -0 "${RUN_PID}" 2>/dev/null; do
        sleep 1
    done
    kill "${TAIL_PID}" 2>/dev/null || true
    wait "${TAIL_PID}" 2>/dev/null || true
fi

kill "${STATUS_PID}" 2>/dev/null || true
wait "${STATUS_PID}" 2>/dev/null || true || true

echo
echo "=== Cluster exited ($(date)) ==="
bash_log "Cluster exited."
if [ -t 0 ]; then
    echo "Press Enter to close this window..."
    read -r _ || true
fi
