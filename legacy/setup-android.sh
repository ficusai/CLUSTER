#!/usr/bin/env bash
# =============================================================================
# Android Worker Setup Script
# Run this INSIDE Termux on the Android device.
#
# Prerequisites:
#   - Install Termux from F-Droid (NOT Google Play)
#   - Run: termux-setup-storage (grant permission)
#   - Connect Android to MacBook Pro via USB
#   - Enable USB tethering on Android
#
# This script:
#   1. Installs build dependencies (clang, cmake, git)
#   2. Clones and builds llama.cpp rpc-server for Android ARM64
#   3. Sets up the worker launch script
# =============================================================================
set -euo pipefail

ANDROID_DIR="${HOME}/ai-cluster"
RPC_PORT="50052"

echo "============================================"
echo "  Android AI Worker Setup (Termux)"
echo "  Target: ${ANDROID_DIR}"
echo "============================================"

# 1. Update packages and install build dependencies
echo "[Android] Updating packages..."
pkg update -y && pkg upgrade -y

echo "[Android] Installing build dependencies..."
pkg install -y git cmake clang make build-essential openssl

# Verify tools
echo "[Android] Checking tools..."
which clang cmake git make

# 2. Create working directory
mkdir -p "${ANDROID_DIR}"
cd "${ANDROID_DIR}"

# 3. Clone and build llama.cpp rpc-server
echo "[Android] Cloning llama.cpp..."
git clone --depth=1 https://github.com/ggml-org/llama.cpp.git
cd llama.cpp

echo "[Android] Building rpc-server for Android ARM64..."
mkdir -p build && cd build

# Build CPU-only rpc-server (no GPU needed for worker)
cmake .. \
    -DGGML_RPC=ON \
    -DGGML_BLAS=OFF \
    -DGGML_VULKAN=OFF \
    -DGGML_LLAMAFILE=OFF \
    -DBUILD_SHARED_LIBS=OFF \
    -DGGML_STATIC=ON \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_COMPILER=clang \
    -DCMAKE_CXX_COMPILER=clang++

make -j$(nproc 2>/dev/null || echo 4) rpc-server

echo "[Android] Build complete!"
cp ../bin/rpc-server "${ANDROID_DIR}/rpc-server"
ls -lh "${ANDROID_DIR}/rpc-server"

# 4. Verify the binary works
echo "[Android] Verifying rpc-server..."
"${ANDROID_DIR}/rpc-server" --help 2>&1 | head -5 && echo "[Android] Binary OK" || echo "[Android] WARNING: Binary may have issues"

# 5. Create config file (write root IP if detected)
if [ -n "${ROOT_IP_CHECK:-}" ]; then
    cat > "${ANDROID_DIR}/android-config.env" << CONFIG
# Android AI Worker Configuration
ROOT_IP="${ROOT_IP_CHECK}"
RPC_PORT="50052"
THREADS="$(nproc 2>/dev/null || echo 4)"
CONFIG
    echo "[Android] Config written to ${ANDROID_DIR}/android-config.env"
fi

# 6. Create launch script (non-interactive, reads config)
cat > "${ANDROID_DIR}/start-worker.sh" << 'SCRIPT'
#!/usr/bin/env bash
# =============================================================================
# Start Android as a worker node in the AI cluster
# =============================================================================
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RPC_BIN="${DIR}/rpc-server"
CONFIG_FILE="${DIR}/android-config.env"

# Load config if available
if [ -f "${CONFIG_FILE}" ]; then
    source "${CONFIG_FILE}"
fi

ROOT_IP="${ROOT_IP:-}"
if [ -z "${ROOT_IP}" ]; then
    echo "[Android] ERROR: ROOT_IP not set."
    echo "  Edit ${CONFIG_FILE} or set ROOT_IP env var."
    exit 1
fi

RPC_PORT="${RPC_PORT:-50052}"
THREADS="${THREADS:-$(nproc 2>/dev/null || echo 4)}"

echo "============================================"
echo "  Android AI Worker"
echo "  Root node: ${ROOT_IP}:${RPC_PORT}"
echo "  Threads: ${THREADS}"
echo "============================================"

cleanup() {
    echo "[Android] Shutting down..."
    kill $RPC_PID 2>/dev/null || true
    wait
}
trap cleanup EXIT INT TERM

"${RPC_BIN}" -H 0.0.0.0 -p "${RPC_PORT}" -t "${THREADS}" -c &
RPC_PID=$!

echo "[Android] Worker running. Press Ctrl+C to stop."
wait
SCRIPT

chmod +x "${ANDROID_DIR}/start-worker.sh"

# 7. Create Termux:Boot script for auto-start on boot
mkdir -p ~/.termux/boot 2>/dev/null || true
if [ -d ~/.termux/boot ]; then
    cat > ~/.termux/boot/start-worker.sh << 'BOOT'
#!/data/data/com.termux/files/usr/bin/bash
# Termux:Boot — AI Cluster Worker autostart
sleep 10
pkill -f rpc-server 2>/dev/null || true
cd ~/ai-cluster
exec ./start-worker.sh
BOOT
    chmod +x ~/.termux/boot/start-worker.sh
    echo "[Android] ✅ Termux:Boot script created at ~/.termux/boot/start-worker.sh"
    echo "[Android]    Worker will start automatically on phone boot!"
fi

echo ""
echo "============================================"
echo "  Android Setup Complete!"
echo ""
echo "  Binary:      ${ANDROID_DIR}/rpc-server"
echo "  Start cmd:   ${ANDROID_DIR}/start-worker.sh"
echo "  Config:      ${ANDROID_DIR}/android-config.env"
echo ""
echo "  Auto-start:  ~/.termux/boot/start-worker.sh (requires Termux:Boot)"
echo "============================================"
