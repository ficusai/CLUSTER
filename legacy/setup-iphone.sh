#!/usr/bin/env bash
# =============================================================================
# Jailbroken iPhone Setup Script
# Run this on the iPhone via SSH (ssh root@<iphone-ip>) or in NewTerm.
#
# This script:
#   1. Installs build dependencies (clang, cmake, git)
#   2. Clones and builds llama.cpp rpc-server for iOS ARM64
#   3. Verifies the binary works
#   4. Tests reachability to the root node
#   5. Sets up the worker launch script
# =============================================================================
set -euo pipefail

IPHONE_DIR="${HOME}/ai-cluster"
RPC_PORT="50052"

echo "============================================"
echo "  iPhone AI Worker Setup"
echo "  Target: ${IPHONE_DIR}"
echo "============================================"

# 1. Install dependencies via apt
echo "[iPhone] Updating packages..."
apt update

echo "[iPhone] Installing build dependencies..."
apt install -y git clang cmake make coreutils findutils python3 python3-pip

# Verify tools
echo "[iPhone] Checking tools..."
which clang cmake git make || {
    echo "[iPhone] ERROR: Required tools not found. Check your jailbreak's APT sources."
    exit 1
}

# 2. Create working directory
mkdir -p "${IPHONE_DIR}"
cd "${IPHONE_DIR}"

# 3. Clone and build llama.cpp rpc-server
if [ -d "llama.cpp" ]; then
    echo "[iPhone] Removing previous llama.cpp clone..."
    rm -rf llama.cpp
fi

echo "[iPhone] Cloning llama.cpp..."
git clone --depth=1 https://github.com/ggml-org/llama.cpp.git
cd llama.cpp

echo "[iPhone] Building rpc-server for iOS ARM64..."
echo "  This may take 5-15 minutes depending on your iPhone's CPU..."
mkdir -p build && cd build

# Build CPU-only rpc-server
cmake .. \
    -DGGML_RPC=ON \
    -DGGML_BLAS=OFF \
    -DGGML_METAL=OFF \
    -DGGML_ACCELERATE=OFF \
    -DGGML_LLAMAFILE=OFF \
    -DBUILD_SHARED_LIBS=OFF \
    -DGGML_STATIC=ON \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_COMPILER=clang \
    -DCMAKE_CXX_COMPILER=clang++ 2>&1

echo "[iPhone] Compiling..."
make -j$(sysctl -n hw.ncpu 2>/dev/null || echo 2) rpc-server 2>&1

echo "[iPhone] Build complete!"
cp ../bin/rpc-server "${IPHONE_DIR}/rpc-server"
ls -lh "${IPHONE_DIR}/rpc-server"

# 4. Verify the binary works
echo "[iPhone] Verifying rpc-server..."
"${IPHONE_DIR}/rpc-server" --help 2>&1 | head -5 && echo "[iPhone] Binary OK" || echo "[iPhone] WARNING: Binary may have issues"

# 5. Get the iPhone's current IP (from USB tether interface)
echo "[iPhone] Checking network interfaces..."
IPHONE_IP=$(ip -4 addr show | grep -E 'ipheth|enx' | grep inet | awk '{print $2}' | cut -d/ -f1 | head -1)
if [ -n "${IPHONE_IP}" ]; then
    echo "[iPhone] iPhone USB IP: ${IPHONE_IP}"
else
    echo "[iPhone] WARNING: Could not detect USB IP. Make sure USB tethering is enabled."
    echo "[iPhone] Settings > Personal Hotspot > Enable (USB Only)"
fi

# 6. Verify connectivity to root node
echo ""
echo -n "Enter root node IP (e.g., 192.168.1.100) or press Enter to skip: "
read ROOT_IP_CHECK
if [ -n "${ROOT_IP_CHECK}" ]; then
    echo "[iPhone] Testing connectivity to root node ${ROOT_IP_CHECK}..."
    if ping -c 2 -W 3 "${ROOT_IP_CHECK}" &>/dev/null; then
        echo "[iPhone] ✅ Root node reachable!"
    else
        echo "[iPhone] ⚠️  Root node not reachable. Check USB tethering and confirm root node is running."
    fi
fi

# 7. Create config file with root IP
if [ -n "${ROOT_IP_CHECK}" ]; then
    cat > "${IPHONE_DIR}/iphone-config.env" << CONFIG
# iPhone AI Worker Configuration
ROOT_IP="${ROOT_IP_CHECK}"
RPC_PORT="50052"
THREADS="$(sysctl -n hw.ncpu 2>/dev/null || echo 4)"
CONFIG
    echo "[iPhone] Config written to ${IPHONE_DIR}/iphone-config.env"
fi

# 8. Create launch script (non-interactive, reads config)
cat > "${IPHONE_DIR}/start-worker.sh" << 'SCRIPT'
#!/usr/bin/env bash
# =============================================================================
# Start the iPhone as a worker node in the AI cluster
# =============================================================================
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RPC_BIN="${DIR}/rpc-server"
CONFIG_FILE="${DIR}/iphone-config.env"

# Load config if available
if [ -f "${CONFIG_FILE}" ]; then
    source "${CONFIG_FILE}"
fi

ROOT_IP="${ROOT_IP:-}"
if [ -z "${ROOT_IP}" ]; then
    echo "[iPhone] ERROR: ROOT_IP not set."
    echo "  Edit ${CONFIG_FILE} or set ROOT_IP env var."
    exit 1
fi

RPC_PORT="${RPC_PORT:-50052}"
THREADS="${THREADS:-$(sysctl -n hw.ncpu 2>/dev/null || echo 4)}"

echo "============================================"
echo "  iPhone AI Worker"
echo "  Root node: ${ROOT_IP}:${RPC_PORT}"
echo "  Threads: ${THREADS}"
echo "============================================"

cleanup() {
    echo "[iPhone] Shutting down..."
    kill $RPC_PID 2>/dev/null || true
    wait
}
trap cleanup EXIT INT TERM

"${RPC_BIN}" -H 0.0.0.0 -p "${RPC_PORT}" -t "${THREADS}" -c &
RPC_PID=$!

echo "[iPhone] Worker running on port ${RPC_PORT}. Press Ctrl+C to stop."
wait
SCRIPT

chmod +x "${IPHONE_DIR}/start-worker.sh"

echo ""
echo "============================================"
echo "  iPhone Setup Complete!"
echo ""
echo "  Binary:      ${IPHONE_DIR}/rpc-server"
echo "  Start cmd:   ${IPHONE_DIR}/start-worker.sh"
echo "  Config:      ${IPHONE_DIR}/iphone-config.env"
echo ""
echo "  Steps to connect to cluster:"
echo "    1. iPhone: Settings > Personal Hotspot > Enable (USB Only)"
echo "    2. Run: ${IPHONE_DIR}/start-worker.sh"
echo "    3. On root node (Fedora), run: ~/Documents/ai-cluster-auto-connect/legacy/start-root.sh"
echo ""
echo "  For auto-start on boot:"
echo "    Create /Library/LaunchDaemons/ai.cluster.worker.plist"
echo "============================================"
