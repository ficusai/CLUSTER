#!/usr/bin/env bash
# Build unified cluster binary for current platform only
# Usage: ./build/build.sh
# Requires: Python 3.8+, PyInstaller (pip install pyinstaller)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_DIR/dist"
SRC_DIR="$PROJECT_DIR/src"
PLATFORM="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

mkdir -p "$DIST_DIR"

echo "=== Building AI Cluster Auto-Connect ==="
echo "Version: $(grep '^VERSION' "$PROJECT_DIR/cluster.py" | head -1 | cut -d'\"' -f2)"
echo "Platform: ${PLATFORM}-${ARCH}"
echo ""

DATA_SEP=":"
[[ "$PLATFORM" == "mingw"* || "$PLATFORM" == "cygwin"* || "$PLATFORM" == "windows"* ]] && DATA_SEP=";"

WORK_DIR="$(mktemp -d -t pyibuild-cluster-XXXXXX)"
trap 'rm -rf "$WORK_DIR"' EXIT

pyinstaller --onefile \
    --name "cluster-${PLATFORM}-${ARCH}" \
    --distpath "$DIST_DIR" \
    --workpath "$WORK_DIR" \
    --add-data "${SRC_DIR}/common${DATA_SEP}common" \
    --add-data "${SRC_DIR}/root${DATA_SEP}root" \
    --add-data "${SRC_DIR}/worker${DATA_SEP}worker" \
    --add-data "${SRC_DIR}/gui${DATA_SEP}gui" \
    --hidden-import "PySide6" \
    --hidden-import "PySide6.QtCore" \
    --hidden-import "PySide6.QtGui" \
    --hidden-import "PySide6.QtWidgets" \
    --hidden-import "zeroconf" \
    --hidden-import "psutil" \
    --hidden-import "yaml" \
    --hidden-import "rich" \
    --hidden-import "rich.console" \
    --hidden-import "rich.table" \
    --hidden-import "rich.panel" \
    --hidden-import "rich.layout" \
    --hidden-import "rich.text" \
    --hidden-import "rich.live" \
    --hidden-import "rich.columns" \
    "$PROJECT_DIR/cluster.py" 2>&1 | tail -5

echo ""
echo "=== Build complete ==="
echo ""
ls -lh "$DIST_DIR/cluster-${PLATFORM}-${ARCH}" 2>/dev/null || ls -lh "$DIST_DIR"
echo ""
echo "To run:"
echo "  $DIST_DIR/cluster-${PLATFORM}-${ARCH}                  # Interactive (terminal)"
echo "  $DIST_DIR/cluster-${PLATFORM}-${ARCH} --root           # Root mode"
echo "  $DIST_DIR/cluster-${PLATFORM}-${ARCH} --worker         # Worker mode"
echo "  $DIST_DIR/cluster-${PLATFORM}-${ARCH} --gui            # Desktop GUI"
echo "  $DIST_DIR/cluster-${PLATFORM}-${ARCH} --root --gui     # Root with desktop GUI"
echo "  $DIST_DIR/cluster-${PLATFORM}-${ARCH} --worker --gui   # Worker with desktop GUI"
echo ""
echo "To install system-wide with desktop integration:"
echo "  sudo ./install.sh"
