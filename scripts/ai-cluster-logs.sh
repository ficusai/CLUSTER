#!/usr/bin/env bash
# Open the AI Cluster root log in a terminal tail view.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"

pick_log() {
    # Preferred order:
    #   1. loghub timestamped files (real session output)
    #   2. desktop-root.log (desktop entry launches)
    #   3. current.log (legacy alias)
    local best=""
    best="$(ls -t "${LOG_DIR}"/*.log 2>/dev/null | grep -vE '(events\.log|launcher\.log|desktop-root\.log|current\.log)' | head -n1 || true)"
    if [ -z "${best}" ]; then
        best="$(ls -t "${LOG_DIR}"/desktop-root.log 2>/dev/null | head -n1 || true)"
    fi
    if [ -z "${best}" ]; then
        best="$(ls -t "${LOG_DIR}"/current.log 2>/dev/null | head -n1 || true)"
    fi
    echo "${best:-}"
}

LOG_FILE="$(pick_log)"
[ -n "${LOG_FILE}" ] && [ -f "${LOG_FILE}" ] || { echo "No log files yet in ${LOG_DIR}"; exit 0; }

run_in_terminal() {
    local cmd="$1"
    if command -v ptyxis &>/dev/null; then
        ptyxis -- bash -c "${cmd}; exec bash" &>/dev/null & return 0
    fi
    if command -v gnome-terminal &>/dev/null; then
        gnome-terminal -- bash -c "${cmd}; exec bash" &>/dev/null & return 0
    fi
    if command -v konsole &>/dev/null; then
        konsole -e bash -c "${cmd}; exec bash" &>/dev/null & return 0
    fi
    if command -v xfce4-terminal &>/dev/null; then
        xfce4-terminal --command="bash -c '${cmd}; exec bash'" &>/dev/null & return 0
    fi
    if command -v alacritty &>/dev/null; then
        alacritty -e bash -c "${cmd}; exec bash" &>/dev/null & return 0
    fi
    if command -v xterm &>/dev/null; then
        xterm -e "bash -c '${cmd}; exec bash'" &>/dev/null & return 0
    fi
    # Last resort: dump to current terminal
    eval "${cmd}"
}

run_in_terminal "tail -n 200 -f '${LOG_FILE}'"
