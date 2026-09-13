#!/usr/bin/env bash
# =============================================================================
# AI Cluster Launcher & Worker Onboarding
# Unified entry point for Linux desktop.
#
# Usage:
#   ./launcher.sh                  Interactive menu (Start Root / Add Device)
#   ./launcher.sh --root           Start as root device
#   ./launcher.sh --add-device     Show device type menu
#   ./launcher.sh --add-device android --usb    Onboard Android via USB
#   ./launcher.sh --add-device android --net    Onboard Android via WiFi
# =============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${PROJECT_DIR}/config.yaml"
SSH_STRICT_HOST_KEY="${SSH_STRICT_HOST_KEY:-accept-new}"
SSH_KEY="${PROJECT_DIR}/legacy/android_ssh_key"

# ── Terminal helpers ──────────────────────────────────────────────────────────
if [ -t 1 ]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; BLUE=''; NC=''
fi
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*"; }
blue()  { echo -e "${BLUE}$*${NC}"; }

press() { echo; read -p "Press Enter to continue... " _; }

log_event() {
    local msg="$1"
    local level="${2:-INFO}"
    local ts
    ts="$(date '+%Y-%m-%d %H:%M:%S')"
    local log_dir="${PROJECT_DIR}/logs"
    mkdir -p "${log_dir}" 2>/dev/null || true
    echo "[${ts}] [${level}] [launcher.sh] ${msg}" >> "${log_dir}/launcher.log"
}

run_in_new_terminal() {
    # Try to open the command in a separate terminal window so the menu stays usable.
    # Preference order: ptyxis, tilix, konsole, xfce4-terminal, kitty, alacritty, xterm
    local cmd="$1"
    shift
    if command -v ptyxis &>/dev/null; then
        ptyxis -- bash -c "$cmd; exec bash" "$@" &>/dev/null & return 0; fi
    if command -v tilix &>/dev/null; then
        tilix -e bash -c "$cmd; exec bash" &>/dev/null & return 0; fi
    if command -v konsole &>/dev/null; then
        konsole -e bash -c "$cmd; exec bash" &>/dev/null & return 0; fi
    if command -v xfce4-terminal &>/dev/null; then
        xfce4-terminal --command="bash -c '$cmd; exec bash'" &>/dev/null & return 0; fi
    if command -v kitty &>/dev/null; then
        kitty @ launch --type=window bash -c "$cmd; exec bash" &>/dev/null & return 0; fi
    if command -v alacritty &>/dev/null; then
        alacritty -e bash -c "$cmd; exec bash" &>/dev/null & return 0; fi
    if command -v xterm &>/dev/null; then
        xterm -e "bash -c '$cmd; exec bash'" &>/dev/null & return 0; fi
    return 1
}

# ── Requirements ──────────────────────────────────────────────────────────────
require() {
    local missing=()
    for cmd in "$@"; do
        command -v "$cmd" &>/dev/null || missing+=("$cmd")
    done
    if [ ${#missing[@]} -gt 0 ]; then
        err "Missing commands: ${missing[*]}"
        err "Install them first, then re-run this script."
        return 1
    fi
}

install_adb_if_missing() {
    if command -v adb &>/dev/null; then return; fi
    info "ADB not found. Attempting to install android-tools..."
    if command -v dnf &>/dev/null; then
        sudo dnf install -y android-tools
    elif command -v apt &>/dev/null; then
        sudo apt update && sudo apt install -y android-tools-adb
    else
        err "Cannot auto-install adb. Please install 'android-tools' manually."
        return 1
    fi
}

# ── Android helpers ────────────────────────────────────────────────────────────
ANDROID_USER_DEFAULT="u0_a377"
ANDROID_SSH_PORT=8022
TERMUX_HOME_GUESS="/data/data/com.termux/files/home"

get_termux_user() {
    # Try common paths to locate the Termux home and its owner
    local home
    home=$(adb shell "ls -d ${TERMUX_HOME_GUESS}/*/" 2>/dev/null | head -1 | tr -d '\r' || true)
    if [ -n "$home" ]; then
        basename "$home"
    else
        echo "$ANDROID_USER_DEFAULT"
    fi
}

get_ip_from_adb_shell() {
    # Returns first non-loopback IPv4 address visible to the shell user
    adb shell "ip -f inet -json addr show" 2>/dev/null \
        | python3 -c "
import sys, json
data = json.load(sys.stdin)
for iface in data:
    for addr in iface.get('addr_info', []):
        ip = addr.get('local', '')
        if ip and not ip.startswith('127.'):
            print(ip)
            sys.exit(0)
" | head -1 | tr -d '\r'
}

find_android_on_network() {
    local subnet="${1:-192.168.1}"
    info "Scanning ${subnet}.0/24 for Termux SSH (port ${ANDROID_SSH_PORT})..."
    local found
    found=$(python3 -c "
import socket, concurrent.futures, ipaddress, sys
subnet = ipaddress.ip_network('${subnet}.0/24')
def check(ip):
    try:
        with socket.create_connection((str(ip), ${ANDROID_SSH_PORT}), timeout=0.8):
            return str(ip)
    except Exception:
        return None
with concurrent.futures.ThreadPoolExecutor(max_workers=120) as ex:
    ips = [ex.submit(check, ip) for ip in subnet.hosts()]
    for f in concurrent.futures.as_completed(ips):
        r = f.result()
        if r:
            print(r)
            sys.exit(0)
" 2>/dev/null || true)
    echo "${found:-}"
}

# ── Start Root ────────────────────────────────────────────────────────────────
stop_old_root() {
    local killed=0
    for sig in TERM KILL; do
        # Match only root cluster, local rpc-server, and local llama-server, not this launcher
        local pids
        pids=$(pgrep -f "${PROJECT_DIR}/.*cluster\\.py --root" 2>/dev/null || true)
        [ -n "$pids" ] && killed=$((killed + $(echo "$pids" | wc -l)))
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -"$sig" 2>/dev/null || true
        fi
        pids=$(pgrep -f "${PROJECT_DIR}/.*rpc-server" 2>/dev/null || true)
        [ -n "$pids" ] && killed=$((killed + $(echo "$pids" | wc -l)))
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -"$sig" 2>/dev/null || true
        fi
        pids=$(pgrep -f "${PROJECT_DIR}/.*llama-server" 2>/dev/null || true)
        [ -n "$pids" ] && killed=$((killed + $(echo "$pids" | wc -l)))
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -"$sig" 2>/dev/null || true
        fi
        [ "$sig" = "TERM" ] && sleep 1
        if ! pgrep -f "${PROJECT_DIR}/.*cluster\\.py --root" >/dev/null 2>&1; then break; fi
    done
    if [ "$killed" -gt 0 ]; then
        warn "Stopped $killed stale cluster process(es)."
        sleep 1
    fi
    # Release common ports if anything is still lingering
    for port in 52053 50052 8080 8081; do
        local leftover
        leftover=$(lsof -ti tcp:"$port" -c python3 -c llama-server -c rpc-server 2>/dev/null | sort -u || true)
        [ -n "$leftover" ] && echo "$leftover" | xargs -r kill -9 2>/dev/null || true
    done
}

start_root() {
    log_event "Selected: Start as Root Device"
    stop_old_root
    info "Starting AI Cluster as ROOT device..."
    cd "$PROJECT_DIR"
    if [ "${AI_CLUSTER_DESKTOP_LAUNCH:-}" = "1" ]; then
        info "Desktop launch: running root cluster in this terminal."
        exec python3 "$PROJECT_DIR/cluster.py" --root
    fi
    if run_in_new_terminal "python3 '$PROJECT_DIR/cluster.py' --root"; then
        info "Root cluster launched in a new terminal window."
        info "You can use this menu to add worker devices while root runs."
        press
    else
        warn "No compatible terminal emulator found. Running in this window."
        warn "The menu will be unavailable until you stop the cluster."
        sleep 1
        exec python3 "$PROJECT_DIR/cluster.py" --root
    fi
}

# ── Onboard Android (Network / SSH) ──────────────────────────────────────────
onboard_android_network() {
    require ssh scp python3

    # Detect local subnet
    LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "")
    SUBNET=""
    if [[ "$LOCAL_IP" =~ ^([0-9]+\.[0-9]+\.[0-9]+)\. ]]; then
        SUBNET="${BASH_REMATCH[1]}"
    else
        read -p "Enter your local subnet (e.g. 192.168.1): " SUBNET
    fi

    # Try auto-discovery first
    ANDROID_IP=$(find_android_on_network "$SUBNET")

    if [ -z "$ANDROID_IP" ]; then
        warn "No Android device with SSH (port ${ANDROID_SSH_PORT}) found on ${SUBNET}.0/24."
        info "Make sure Termux is installed on your Android phone, sshd is running,"
        info "and the phone is on the same WiFi network."
        info ""
        info "To enable SSH on Android (Termux):"
        info "  1. Open Termux app"
        info "  2. Run:  pkg update && pkg install -y openssh"
        info "  3. Run:  passwd          (set a password, OR skip if using keys only)"
        info "  4. Run:  sshd"
        info "  5. Run:  ifconfig        (note your IP address)"
        echo
        read -p "Enter Android IP manually: " ANDROID_IP
        if [ -z "$ANDROID_IP" ]; then
            err "No IP provided. Aborting."
            return 1
        fi
    else
        info "Found Android device at ${ANDROID_IP}"
    fi

    # Verify SSH connectivity
    info "Verifying SSH to ${ANDROID_IP}..."
    if ! ssh -i "$SSH_KEY" -o StrictHostKeyChecking=${SSH_STRICT_HOST_KEY} -o ConnectTimeout=6 \
            -p "$ANDROID_SSH_PORT" "$ANDROID_USER_DEFAULT@$ANDROID_IP" "true" 2>/dev/null; then
        err "SSH connection failed. Check IP, sshd status, and keys."
        return 1
    fi
    info "SSH connection OK."

    # Deploy project
    SSH_BASE="ssh -i $SSH_KEY -o StrictHostKeyChecking=${SSH_STRICT_HOST_KEY} -o ServerAliveInterval=15 -o TCPKeepAlive=yes -p $ANDROID_SSH_PORT $ANDROID_USER_DEFAULT@$ANDROID_IP"

    info "Copying project files to Android..."
    tar -C "$PROJECT_DIR" -cf - \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.log' \
        --exclude='dist' \
        --exclude='build' \
        . | $SSH_BASE "mkdir -p ~/ai-cluster && tar -C ~/ai-cluster -xf -"

    info "Installing Python dependencies on Android..."
    $SSH_BASE "cd ~/ai-cluster && pkg update -y && pkg install -y python git openssh && pip install pyyaml zeroconf psutil rich"

    # Ensure sshd restarts on boot (no-op if Termux:Boot not installed)
    $SSH_BASE "mkdir -p ~/.termux/boot 2>/dev/null || true"
    $SSH_BASE "cat > ~/.termux/boot/sshd << 'EOF'\n#!/data/data/com.termux/files/usr/bin/bash\nsshd\nEOF" || true
    $SSH_BASE "chmod +x ~/.termux/boot/sshd" || true

    info "Starting worker on Android..."
    $SSH_BASE "cd ~/ai-cluster && nohup python3 src/worker/main.py > worker.log 2>&1 &"

    info "Android worker deployed to ${ANDROID_IP}"
    echo
    blue "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    blue "  Android worker started!"
    blue "  Device:  ${ANDROID_IP}"
    blue "  Logs:    ai-cluster-auto-connect/legacy/android-log-${ANDROID_IP}.log"
    blue "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ── Onboard Android (USB / ADB) ───────────────────────────────────────────────
onboard_android_usb() {
    require python3

    if ! command -v adb &>/dev/null; then
        install_adb_if_missing || return 1
    fi

    info "Waiting for Android device via USB..."
    # Wait up to 30s for device
    for i in $(seq 1 30); do
        if adb get-state 2>/dev/null | grep -qi device; then
            break
        fi
        sleep 1
    done
    if ! adb get-state 2>/dev/null | grep -qi device; then
        err "No Android device detected via USB."
        err "Please enable USB debugging and trust this computer."
        return 1
    fi

    ANDROID_USER=$(get_termux_user)
    info "Detected Termux user: ${ANDROID_USER}"

    # Push setup helper
    info "Pushing setup script to shared storage..."
    adb push "$PROJECT_DIR/setup-termux.sh" /sdcard/Download/ai-cluster-setup.sh

    # Check if sshd is already accessible from via some interface
    ANDROID_IP=$(get_ip_from_adb_shell)
    if [ -n "$ANDROID_IP" ] && ssh -i "$SSH_KEY" -o StrictHostKeyChecking=${SSH_STRICT_HOST_KEY} -o ConnectTimeout=4 \
            -p "$ANDROID_SSH_PORT" "$ANDROID_USER_DEFAULT@$ANDROID_IP" "true" 2>/dev/null; then
        info "Android SSH already reachable at ${ANDROID_IP}. Switched to network workflow."
        onboard_android_network_preconf "$ANDROID_IP"
        return $?
    fi

    echo
    warn "Termux SSH is not set up yet."
    info "Please do the following on your Android phone:"
    blue "  1. Open the Termux app"
    blue "  2. Paste and run this command:"
    blue ""
    blue "     bash /sdcard/Download/ai-cluster-setup.sh"
    blue ""
    info "This will install dependencies and start the SSH daemon."
    info "It takes about 2 minutes depending on your connection."
    echo
    read -p "Press Enter once it finishes in Termux... "

    # Re-detect IP after setup
    sleep 2
    ANDROID_IP=$(get_ip_from_adb_shell)

    if [ -z "$ANDROID_IP" ]; then
        ANDROID_IP="${ANDROID_IP:-"192.168.42.129"}"
    fi

    info "Attempting SSH at ${ANDROID_IP}..."
    for i in $(seq 1 10); do
        if ssh -i "$SSH_KEY" -o StrictHostKeyChecking=${SSH_STRICT_HOST_KEY} -o ConnectTimeout=4 \
                -p "$ANDROID_SSH_PORT" "$ANDROID_USER_DEFAULT@$ANDROID_IP" "true"; then
            break
        fi
        sleep 2
    done

    if ! ssh -i "$SSH_KEY" -o StrictHostKeyChecking=${SSH_STRICT_HOST_KEY} -o ConnectTimeout=4 \
            -p "$ANDROID_SSH_PORT" "$ANDROID_USER_DEFAULT@$ANDROID_IP" "true"; then
        err "SSH still not available. Did 'sshd' show 'listening on port 8022' in Termux?"
        return 1
    fi

    onboard_android_network_preconf "$ANDROID_IP"
}

# Shared SSH-based deployment (used by both USB and Network paths)
onboard_android_network_preconf() {
    local ip="$1"
    local SSH_BASE="ssh -i $SSH_KEY -o StrictHostKeyChecking=${SSH_STRICT_HOST_KEY} -o ServerAliveInterval=15 -o TCPKeepAlive=yes -p $ANDROID_SSH_PORT $ANDROID_USER_DEFAULT@$ip"

    info "Deploying project to ${ip}..."
    tar -C "$PROJECT_DIR" -cf - \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.log' \
        --exclude='dist' \
        --exclude='build' \
        . | $SSH_BASE "mkdir -p ~/ai-cluster && tar -C ~/ai-cluster -xf -"

    info "Installing Python dependencies..."
    $SSH_BASE "cd ~/ai-cluster && pkg update -y && pkg install -y python git openssh && pip install pyyaml zeroconf psutil rich"

    info "Starting worker..."
    $SSH_BASE "cd ~/ai-cluster && nohup python3 src/worker/main.py > worker.log 2>&1 &"

    info "Done. Android worker is running at ${ip}"
    echo
    blue "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    blue "  Android worker started!"
    blue "  Device:  ${ip}"
    blue "  Logs:    tail -f worker.log   (via SSH to ${ip})"
    blue "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ── Onboard iOS ───────────────────────────────────────────────────────────────
onboard_ios() {
    warn "iOS onboarding is not yet automated (macOS host required for iOS builds)."
    info "See IMPLEMENTATION-PLAN.md for roadmap."
}

# ── Onboard Windows ───────────────────────────────────────────────────────────
onboard_windows() {
    warn "Windows onboarding is not yet automated."
    info "See IMPLEMENTATION-PLAN.md for roadmap."
}

# ── Onboard Linux ─────────────────────────────────────────────────────────────
onboard_linux() {
    warn "Linux onboarding is not yet automated."
    info "On a target Linux machine: clone this repo and run 'python3 src/worker/main.py'"
}

# ── Menus ─────────────────────────────────────────────────────────────────────
select_device() {
    log_event "Entered select_device menu"
    echo
    blue "Select device type to add as worker:"
    echo "  [1] Android"
    echo "  [2] iOS"
    echo "  [3] Windows"
    echo "  [4] Linux"
    echo "  [5] Back"
    printf "  Enter choice: "
    read -r c
    case "$c" in
        1) onboard_android_menu ;;
        2) onboard_ios ;;
        3) onboard_windows ;;
        4) onboard_linux ;;
        *) return ;;
    esac
}

onboard_android_menu() {
    echo
    blue "Select Android connection method:"
    echo "  [1] USB (ADB)"
    echo "  [2] Network (WiFi)"
    echo "  [3] Back"
    printf "  Enter choice: "
    read -r c
    case "$c" in
        1) onboard_android_usb ;;
        2) onboard_android_network ;;
        *) return ;;
    esac
}

interactive_menu() {
    log_event "Entered interactive menu"
    while true; do
        clear
        blue "═══════════════════════════════════════════"
        blue "       AI Cluster Launcher"
        blue "═══════════════════════════════════════════"
        echo
        echo "  [1] Start as Root Device"
        echo "  [2] Add Worker Device"
        echo "  [3] Quit"
        echo
        printf "  Enter choice: "
        read -r c
        case "$c" in
            1) start_root ;;
            2) select_device ;;
            3) exit 0 ;;
            *) warn "Invalid choice."; sleep 1 ;;
        esac
    done
}

# ── Main ──────────────────────────────────────────────────────────────────────
# Ensure we have an interactive terminal for menus
if [ ! -t 0 ]; then
    warn "No interactive terminal detected. Starting as Root by default."
    echo "  To use the menu, launch this script from a terminal instead."
    echo
    sleep 2
    start_root
    exit $?
fi

case "${1:-}" in
    --root)
        log_event "Invoked: --root"
        start_root
        ;;
    --add-device)
        log_event "Invoked: --add-device"
        select_device
        ;;
    *)
        log_event "Invoked: default interactive menu"
        interactive_menu
        ;;
esac
