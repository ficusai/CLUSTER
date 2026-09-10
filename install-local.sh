#!/usr/bin/env bash
# AI Cluster Auto-Connect — User-Level Installer
# Installs to ~/.local/ for desktop integration without root.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${PREFIX:-${HOME}/.local}"
BIN_DIR="${BIN_DIR:-${PREFIX}/bin}"
BIN_NAME="ai-cluster"
BIN_PATH="${BIN_DIR}/${BIN_NAME}"
ICON_DIR="${ICON_DIR:-${PREFIX}/share/icons/hicolor/scalable/apps}"
DESKTOP_DIR="${DESKTOP_DIR:-${PREFIX}/share/applications}"
DATA_DIR="${DATA_DIR:-${PREFIX}/share/ai-cluster}"

if [ "${1:-}" = "--uninstall" ] || [ "${1:-}" = "uninstall" ]; then
    echo "=== Uninstalling AI Cluster (User Install) ==="
    rm -f "${BIN_PATH}"
    rm -f "${ICON_DIR}/ai-cluster.svg"
    rm -f "${DESKTOP_DIR}/ai-cluster"*.desktop
    rm -rf "${DATA_DIR}"
    gtk-update-icon-cache "${HOME}/.local/share/icons/hicolor/" 2>/dev/null || true
    echo "Uninstalled from ${PREFIX}."
    exit 0
fi

echo "=== AI Cluster Auto-Connect (User Install) ==="
echo ""

# Create directories
mkdir -p "$(dirname "${BIN_PATH}")"
mkdir -p "${ICON_DIR}"
mkdir -p "${DESKTOP_DIR}"
mkdir -p "${DATA_DIR}"

# Find the built binary in the project's dist/ folder
DIST_DIR="${SCRIPT_DIR}/dist"
PLATFORM="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
LATEST_BINARY="${DIST_DIR}/cluster-${PLATFORM}-${ARCH}"

echo "[1/3] Installing binary..."
if [ -f "$LATEST_BINARY" ]; then
    install -m 755 "$LATEST_BINARY" "$BIN_PATH"
    echo "  Installed to ${BIN_PATH}"
else
    FOUND=$(ls -t "${DIST_DIR}"/cluster-* 2>/dev/null | head -1 || true)
    if [ -n "$FOUND" ]; then
        install -m 755 "$FOUND" "$BIN_PATH"
        echo "  Installed ${FOUND} to ${BIN_PATH}"
    else
        echo "  No built binary found in ${DIST_DIR}. Using Python fallback mode..."
        echo "  Installing Python dependencies..."
        python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt"
        cat > "${BIN_PATH}" << EOF
#!/usr/bin/env bash
exec python3 "${SCRIPT_DIR}/cluster.py" "\$@"
EOF
        chmod +x "${BIN_PATH}"
        echo "  Installed script wrapper to ${BIN_PATH}"
    fi
fi

# Ensure ~/.local/bin is in PATH
if [[ ":${PATH}:" != *":${HOME}/.local/bin:"* ]]; then
    echo ""
    echo "  NOTE: Add ~/.local/bin to your PATH:"
    echo "    echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
    echo "    source ~/.bashrc"
fi

echo "[2/3] Installing application icon..."
cat > "${ICON_DIR}/ai-cluster.svg" << 'SVG'
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
gtk-update-icon-cache "${HOME}/.local/share/icons/hicolor/" 2>/dev/null || true
echo "  Done."

echo "[3/3] Installing desktop entries..."
for DESKTOP_FILE in "${SCRIPT_DIR}/linux/"*.desktop; do
    if [ -f "$DESKTOP_FILE" ]; then
        BASENAME=$(basename "$DESKTOP_FILE")
        sed "s|/usr/local/bin/ai-cluster|${BIN_PATH}|g" "$DESKTOP_FILE" \
            > "${DESKTOP_DIR}/${BASENAME}"
        echo "  Installed ${BASENAME}"
    fi
done
echo "  Done."

echo ""
echo "=== Installation Complete ==="
echo ""
echo "To start:"
echo "  ai-cluster                    Interactive (terminal)"
echo "  ai-cluster --root              Run as root coordinator"
echo "  ai-cluster --worker            Run as worker node"
echo "  ai-cluster --gui               Desktop GUI (interactive)"
echo "  ai-cluster --root --gui        Desktop GUI as root"
echo "  ai-cluster --worker --gui      Desktop GUI as worker"
echo ""
echo "Look for 'AI Cluster' in your application menu."
echo ""
