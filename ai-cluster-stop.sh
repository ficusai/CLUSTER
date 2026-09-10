#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${APP_DIR}/.run.log"
PID_FILE="${APP_DIR}/.run.pid"

mkdir -p "$(dirname "${LOG_FILE}")" 2>/dev/null || true
export CLUSTER_LAUNCH_START="$(date '+%Y-%m-%d %H:%M:%S')"

ANY_STOPPED=0

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

log "=== Stop script started at ${CLUSTER_LAUNCH_START} ==="
log "APP_DIR=${APP_DIR}"
log "USER=${USER:-$(whoami)}"
log "HOME=${HOME}"
log "PATH=${PATH}"

stop_pid() {
  local pid="$1"
  local name
  name="$(ps -p "${pid}" -o comm= 2>/dev/null || echo "unknown")"
  log "Stopping PID=${pid} (${name})..."
  if kill -0 "${pid}" 2>/dev/null; then
    # Kill the whole process group when this PID is a session leader.
    kill -TERM -"${pid}" 2>/dev/null || kill -TERM "${pid}" 2>/dev/null || true
    sleep 1
    if kill -0 "${pid}" 2>/dev/null; then
      log "PID ${pid} still alive after SIGTERM, sending SIGKILL."
      kill -KILL -"${pid}" 2>/dev/null || kill -KILL "${pid}" 2>/dev/null || true
      sleep 0.3
    fi
    if kill -0 "${pid}" 2>/dev/null; then
      log_failed "Process ${pid} still alive after SIGKILL"
      send_notify "AI Cluster" "Failed to stop PID ${pid}"
      echo "ERROR: Process ${pid} still alive after SIGKILL."
      read -p "Press Enter to close..." _ || true
      return 1
    fi
    log_success "Killed PID ${pid} (${name})"
    echo "Killed PID ${pid} (${name})."
    return 0
  else
    log "Process ${pid} not running (stale PID file?)."
    echo "Process ${pid} not running (stale PID file?)."
    return 1
  fi
}

# 1) PID file from run/events wrappers
if [ -f "${PID_FILE}" ]; then
  pid="$(cat "${PID_FILE}" 2>/dev/null || true)"
  if [ -n "${pid}" ]; then
    if kill -0 "${pid}" 2>/dev/null; then
      stop_pid "${pid}" && ANY_STOPPED=1 || true
    else
      log "Stale PID file at ${PID_FILE}."
      echo "Stale PID file at ${PID_FILE}."
    fi
  fi
  rm -f "${PID_FILE}"
fi

# 2) Known cluster process patterns owned by this project
stop_pattern() {
  local pattern="$1"
  local label="$2"
  log "Scanning for ${label}..."
  local pids
  pids=$(pgrep -f "${pattern}" 2>/dev/null || true)
  if [ -n "${pids}" ]; then
    echo "Stopping ${label}..."
    local stopped=0
    for p in ${pids}; do
      if kill -0 "${p}" 2>/dev/null; then
        if stop_pid "${p}"; then
          stopped=1
        fi
      fi
    done
    if [ "${stopped}" -eq 1 ]; then
      log_success "Stopped ${label}"
      echo "Stopped ${label}."
      ANY_STOPPED=1
    else
      log "No live processes matched ${label}"
    fi
  fi
}

stop_pattern "${APP_DIR}/cluster-supervisor.sh" "cluster supervisor"
stop_pattern "${APP_DIR}/quick-start-cluster.sh" "quick-start launcher"
stop_pattern "${APP_DIR}/ai-cluster-events.sh" "events window"
stop_pattern "${APP_DIR}/.*llama-server" "llama server"
stop_pattern "${APP_DIR}/.*rpc-server" "rpc server"
stop_pattern "${APP_DIR}/dist/cluster-linux-x86_64" "cluster binary (linux)"
stop_pattern "python3 .*${APP_DIR}/cluster\.py" "cluster binary (python)"

# 3) Clean stale PID files
for f in "${PID_FILE}"; do
  if [ -f "${f}" ]; then
    pid="$(cat "${f}" 2>/dev/null || true)"
    if [ -n "${pid}" ] && ! kill -0 "${pid}" 2>/dev/null; then
      rm -f "${f}"
      log "Removed stale PID file ${f}."
    fi
  fi
done

if [ "${ANY_STOPPED}" -eq 1 ]; then
  log_success "All ai-cluster processes stopped."
  echo "All ai-cluster processes stopped."
  send_notify "AI Cluster" "All processes stopped"
else
  log "No running ai-cluster processes found."
  echo "No running ai-cluster processes found."
fi

if [ -t 0 ]; then
    read -p "Press Enter to close..." _ || true
fi
