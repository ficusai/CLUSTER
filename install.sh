#!/usr/bin/env bash
# AI Cluster Auto-Connect — Production Installer for Linux
# Installs systemd services, desktop entries, and the cluster binary.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_NAME="ai-cluster"
BIN_PATH="/usr/local/bin/${BIN_NAME}"
ICON_DIR="/usr/share/icons/hicolor/scalable/apps"
ICON_PATH="${ICON_DIR}/ai-cluster.svg"
DESKTOP_DIR="/usr/share/applications"
SERVICE_DIR="/etc/systemd/system"

echo "=== AI Cluster Auto-Connect Installer ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "This installer requires root privileges for system-wide installation."
    echo "Running with sudo..."
    exec sudo "$0" "$@"
fi

# Install Python dependencies
echo "[1/5] Installing Python dependencies..."
pip3 install --quiet --upgrade pip 2>/dev/null || true
pip3 install --quiet pyyaml zeroconf psutil rich 2>/dev/null || true
echo "  Done."

# Build the binary
echo "[2/5] Building executable..."
BUILD_SCRIPT="${SCRIPT_DIR}/build/build.sh"
if [ -f "$BUILD_SCRIPT" ]; then
    bash "$BUILD_SCRIPT"
else
    echo "  Build script not found at ${BUILD_SCRIPT}"
    echo "  Skipping build step. Install PyInstaller and run build/build.sh manually."
fi

# Find the built binary
DIST_DIR="${SCRIPT_DIR}/dist"
PLATFORM="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
LATEST_BINARY="${DIST_DIR}/cluster-${PLATFORM}-${ARCH}"

if [ -f "$LATEST_BINARY" ]; then
    echo "  Installing binary to ${BIN_PATH}..."
    install -m 755 "$LATEST_BINARY" "$BIN_PATH"
else
    # Try to find any binary in dist
    FOUND=$(ls -t "${DIST_DIR}"/cluster-* 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
        echo "  Installing ${FOUND} to ${BIN_PATH}..."
        install -m 755 "$FOUND" "$BIN_PATH"
    else
        echo "  WARNING: No built binary found. Install PyInstaller and run build/build.sh first."
        echo "  The ai-cluster command will not be available until a binary is built."
    fi
fi

# Install icon
echo "[3/5] Installing application icon..."
mkdir -p "$ICON_DIR"
cat > "$ICON_PATH" << 'SVG'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#4A90D9"/>
      <stop offset="100%" style="stop-color:#2C5F8A"/>
    </linearGradient>
    <linearGradient id="dot" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#50E3C2"/>
      <stop offset="100%" style="stop-color:#2ECC71"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="12" fill="url(#bg)"/>
  <circle cx="32" cy="20" r="8" fill="#fff" opacity="0.9"/>
  <circle cx="16" cy="44" r="7" fill="#fff" opacity="0.7"/>
  <circle cx="48" cy="44" r="7" fill="#fff" opacity="0.7"/>
  <line x1="32" y1="28" x2="16" y2="37" stroke="#fff" stroke-width="2" opacity="0.5"/>
  <line x1="32" y1="28" x2="48" y2="37" stroke="#fff" stroke-width="2" opacity="0.5"/>
  <circle cx="32" cy="20" r="4" fill="url(#dot)"/>
  <circle cx="16" cy="44" r="3.5" fill="#50E3C2"/>
  <circle cx="48" cy="44" r="3.5" fill="#50E3C2"/>
</svg>
SVG
gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
echo "  Done."

# Install desktop entries
echo "[4/5] Installing desktop entries..."
for DESKTOP_FILE in "${SCRIPT_DIR}/linux/"*.desktop; do
    if [ -f "$DESKTOP_FILE" ]; then
        install -m 644 "$DESKTOP_FILE" "${DESKTOP_DIR}/"
        echo "  Installed $(basename "$DESKTOP_FILE")"
    fi
done
echo "  Done."

# Install systemd service files
echo "[5/5] Installing systemd services..."
for SERVICE_FILE in "${SCRIPT_DIR}/linux/"*.service; do
    if [ -f "$SERVICE_FILE" ]; then
        install -m 644 "$SERVICE_FILE" "${SERVICE_DIR}/"
        echo "  Installed $(basename "$SERVICE_FILE")"
    fi
done
systemctl daemon-reload 2>/dev/null || true
echo "  Done."

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Available commands:"
echo "  ai-cluster                    Interactive mode (terminal)"
echo "  ai-cluster --root              Run as root coordinator"
echo "  ai-cluster --worker            Run as worker node"
echo "  ai-cluster --gui               Desktop GUI (interactive)"
echo "  ai-cluster --root --gui        Desktop GUI as root"
echo "  ai-cluster --worker --gui      Desktop GUI as worker"
echo ""
echo "Available systemd services:"
echo "  sudo systemctl enable ai-cluster-root.service    # Start root on boot"
echo "  sudo systemctl enable ai-cluster-worker.service  # Start worker on boot"
echo "  sudo systemctl enable ai-cluster-gui.service     # Start GUI on login"
echo ""
echo "Desktop entries installed; look for 'AI Cluster' in your app menu."
echo ""
