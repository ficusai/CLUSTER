#!/usr/bin/env bash
# =============================================================================
# AI Cluster — Root-side Auto Onboard
# Discovers and connects helper devices (Android/Termux, Linux, etc.)
# with minimal/no manual work on the helper nodes.
# All operations are driven from this root machine via SSH.
# =============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"
mkdir -p "${LOG_DIR}" 2>/dev/null || true
LOG_FILE="${LOG_DIR}/auto-onboard.log"

# Config
SSH_KEY="${PROJECT_DIR}/legacy/android_ssh_key"
ANDROID_SSH_PORT=8022
LINUX_SSH_PORT=22
CONNECT_TIMEOUT=5

# Logging
log() {
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[${ts}] $*" | tee -a "${LOG_FILE}"
}
info()  { log "INFO  $*"; }
warn()  { log "WARN  $*"; }
err()   { log "ERROR $*"; }
ok()    { log "OK    $*"; }

# Detect local subnet
detect_subnet() {
    local ip
    ip="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
    if [[ "$ip" =~ ^([0-9]+\.[0-9]+\.[0-9]+)\. ]]; then
        echo "${BASH_REMATCH[1]}"
        return 0
    fi
    ip -f inet addr show 2>/dev/null \
        | awk '/inet /{print $2}' | head -n1 | cut -d. -f1-3 || true
}

start_worker_remote() {
    local SSH_BASE="$1"
    local ROOT_IP="$2"
    ${SSH_BASE} "pkill -f 'python3 src/worker/main.py' >/dev/null 2>&1 || true; cd ~/ai-cluster && if command -v tmux >/dev/null 2>&1; then tmux kill-session -t ai-worker >/dev/null 2>&1 || true; tmux new-session -d -s ai-worker 'python3 src/worker/main.py --ai-mode --root-ip ${ROOT_IP} >> worker.log 2>&1'; else nohup python3 src/worker/main.py --ai-mode --root-ip ${ROOT_IP} < /dev/null >> worker.log 2>&1 & disown; fi" >/dev/null 2>&1 || true
}

onboard_android() {
    local ip="$1"
    local user="${2:-u0_a377}"
    local SSH_BASE="ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=${CONNECT_TIMEOUT} -o ServerAliveInterval=15 -o TCPKeepAlive=yes -p ${ANDROID_SSH_PORT} ${user}@${ip}"

    info "Android ${ip}: verifying SSH..."
    if ! ${SSH_BASE} "true" >/dev/null 2>&1; then
        warn "Android ${ip}: SSH failed."
        return 1
    fi
    ok "Android ${ip}: SSH OK"

    info "Android ${ip}: deploying project..."
    _deploy_rc=0
    tar -C "${PROJECT_DIR}" -cf - \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.log' \
        --exclude='dist' \
        --exclude='build' \
        . | timeout 600s ${SSH_BASE} "mkdir -p ~/ai-cluster && tar -C ~/ai-cluster -xf -" || _deploy_rc=$?
    if [ "${_deploy_rc}" -ne 0 ]; then
        warn "Android ${ip}: deploy failed (rc=${_deploy_rc}, timeout=600s)."
    fi
    ok "Android ${ip}: project deployed"

    info "Android ${ip}: installing dependencies..."
    ${SSH_BASE} "pkg update -y && pkg install -y python git openssh" >/dev/null 2>&1 || true
    ${SSH_BASE} "python3 -m ensurepip" >/dev/null 2>&1 || true
    ${SSH_BASE} "python3 -m pip install --upgrade pyyaml rich zeroconf" >/dev/null 2>&1 || true
    # psutil is not available on Android in current form; worker has fallback

    info "Android ${ip}: starting worker..."
    local ROOT_IP
    ROOT_IP="$(hostname -I 2>/dev/null | awk '{print $1}' || echo '10.0.0.103')"
    start_worker_remote "${SSH_BASE}" "${ROOT_IP}"

    sleep 2
    if ${SSH_BASE} "pgrep -f 'python3 src/worker/main.py' >/dev/null 2>&1"; then
        ok "Android ${ip}: worker started"
    else
        warn "Android ${ip}: worker may not have started (check worker.log)"
    fi
}

onboard_linux() {
    local ip="$1"
    local user="${2:-ficus-pro}"
    local SSH_BASE="ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=${CONNECT_TIMEOUT} -o ServerAliveInterval=15 -o TCPKeepAlive=yes -p ${LINUX_SSH_PORT} ${user}@${ip}"

    info "Linux ${ip}: verifying SSH..."
    if ! ${SSH_BASE} "true" >/dev/null 2>&1; then
        warn "Linux ${ip}: SSH failed."
        return 1
    fi
    ok "Linux ${ip}: SSH OK"

    info "Linux ${ip}: deploying project..."
    _deploy_rc=0
    tar -C "${PROJECT_DIR}" -cf - \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.log' \
        --exclude='dist' \
        --exclude='build' \
        . | timeout 600s ${SSH_BASE} "mkdir -p ~/ai-cluster && tar -C ~/ai-cluster -xf -" || _deploy_rc=$?
    if [ "${_deploy_rc}" -ne 0 ]; then
        warn "Linux ${ip}: deploy failed (rc=${_deploy_rc}, timeout=600s)."
    fi
    ok "Linux ${ip}: project deployed"

    info "Linux ${ip}: installing dependencies (best-effort)..."
    ${SSH_BASE} "python3 -m pip install --user --upgrade pyyaml zeroconf psutil rich" >/dev/null 2>&1 || true

    info "Linux ${ip}: starting worker..."
    local ROOT_IP
    ROOT_IP="$(hostname -I 2>/dev/null | awk '{print $1}' || echo '10.0.0.103')"
    start_worker_remote "${SSH_BASE}" "${ROOT_IP}"

    sleep 2
    if ${SSH_BASE} "pgrep -f 'python3 src/worker/main.py' >/dev/null 2>&1"; then
        ok "Linux ${ip}: worker started"
    else
        warn "Linux ${ip}: worker may not have started (check worker.log)"
    fi
}

scan_and_onboard() {
    local subnet="$1"
    local tmpfile
    tmpfile="$(mktemp)"
    trap 'rm -f "${tmpfile}"' RETURN

    info "Scanning ${subnet}.0/24 for SSH (ports ${ANDROID_SSH_PORT}, ${LINUX_SSH_PORT})..."

    python3 - "$subnet" "${ANDROID_SSH_PORT}" "${LINUX_SSH_PORT}" > "${tmpfile}" <<'PYEOF'
import socket, ipaddress, sys, concurrent.futures
subnet = ipaddress.ip_network(sys.argv[1] + '.0/24')
ports = [int(sys.argv[2]), int(sys.argv[3])]
def check(port, ip):
    try:
        with socket.create_connection((str(ip), port), timeout=0.5):
            return port, str(ip)
    except Exception:
        return None
with concurrent.futures.ThreadPoolExecutor(max_workers=120) as ex:
    tasks = [ex.submit(check, p, ip) for ip in subnet.hosts() for p in ports]
    for f in concurrent.futures.as_completed(tasks):
        r = f.result()
        if r:
            sys.stdout.write(f"{r[0]} {r[1]}\n")
            sys.stdout.flush()
PYEOF

    if [ ! -s "${tmpfile}" ]; then
        info "No SSH devices found on ${subnet}.0/24."
        return 0
    fi

    info "Discovered candidate(s):"
    while read -r port ip; do
        log "  candidate: ${ip}:${port}"
    done < "${tmpfile}"

    while read -r port ip; do
        if [ "$port" -eq "${ANDROID_SSH_PORT}" ]; then
            onboard_android "$ip" "u0_a377" || true
        elif [ "$port" -eq "${LINUX_SSH_PORT}" ]; then
            onboard_linux "$ip" "ficus-pro" || true
        else
            warn "Unknown SSH port ${port} for ${ip}; skipping."
        fi
    done < "${tmpfile}"
}

# Load user overrides from config if available
USER_ANDROID="u0_a377"
USER_LINUX="ficus-pro"
if [ -f "${PROJECT_DIR}/config.yaml" ]; then
    if command -v python3 >/dev/null 2>&1; then
        cfg_android_user="$(python3 -c "
import yaml, sys
try:
    cfg=yaml.safe_load(open('${PROJECT_DIR}/config.yaml'))
    print(cfg.get('workers',{}).get('deploy_credentials',{}).get('android',{}).get('user',''))
except Exception:
    pass
" 2>/dev/null || true)"
        cfg_linux_user="$(python3 -c "
import yaml, sys
try:
    cfg=yaml.safe_load(open('${PROJECT_DIR}/config.yaml'))
    print(cfg.get('workers',{}).get('deploy_credentials',{}).get('linux',{}).get('user',''))
except Exception:
    pass
" 2>/dev/null || true)"
        [ -n "$cfg_android_user" ] && USER_ANDROID="$cfg_android_user"
        [ -n "$cfg_linux_user" ] && USER_LINUX="$cfg_linux_user"
    fi
fi

SUBNET="$(detect_subnet)"
if [ -z "$SUBNET" ]; then
    err "Could not detect local subnet. Set SUBNET env var or pass as \$1."
    exit 1
fi

info "Starting auto-onboard on subnet ${SUBNET}.0/24"
info "Android default user: ${USER_ANDROID}"
info "Linux default user: ${USER_LINUX}"

# If a specific IP was passed, operate only on that host
if [ $# -ge 1 ]; then
    TARGET="$1"
    if [[ "$TARGET" == *":"* ]]; then
        ip="${TARGET%%:*}"
        port="${TARGET##*:}"
    else
        ip="$TARGET"
        port=""
    fi
    if [ "$port" = "${ANDROID_SSH_PORT}" ] 2>/dev/null; then
        onboard_android "$ip" "$USER_ANDROID" || true
    elif [ "$port" = "${LINUX_SSH_PORT}" ] 2>/dev/null; then
        onboard_linux "$ip" "$USER_LINUX" || true
    elif [ -n "$port" ]; then
        onboard_android "$ip" "$USER_ANDROID" || true
    else
        onboard_android "$ip" "$USER_ANDROID" || true
        onboard_linux "$ip" "$USER_LINUX" || true
    fi
    exit 0
fi

scan_and_onboard "$SUBNET"

info "Auto-onboard pass complete."
