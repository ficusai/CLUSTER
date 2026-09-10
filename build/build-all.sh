#!/usr/bin/env bash
# build-all.sh — Cross-platform PyInstaller build runner
# Usage:
#   ./build/build-all.sh            # build for current platform only
#   ./build/build-all.sh linux      # build linux binary
#   ./build/build-all.sh darwin     # build macos binary (must run on macOS)
#   ./build/build-all.sh mingw      # build windows binary (must run on Windows/MinGW)
#   ./build/build-all.sh all        # build all platforms this host supports
#
# True cross-compilation requires separate build hosts.
# This script documents the supported matrix and attempts local builds.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
mkdir -p "${PROJECT_DIR}/dist" "${PROJECT_DIR}/build"

build_one() {
    local platform="$1"
    local arch="$2"
    local bin_name="cluster-${platform}-${arch}"
    local work_dir="/tmp/pyibuild-${platform}-${arch}"
    mkdir -p "$work_dir"

    echo "=== Building ${bin_name} ==="
    python3 -m PyInstaller \
        --onefile \
        --name "${bin_name}" \
        --distpath "${PROJECT_DIR}/dist" \
        --workpath "$work_dir" \
        --specpath "${PROJECT_DIR}/dist" \
        --add-data "${PROJECT_DIR}/src/common:common" \
        --add-data "${PROJECT_DIR}/src/root:root" \
        --add-data "${PROJECT_DIR}/src/worker:worker" \
        --add-data "${PROJECT_DIR}/src/gui:gui" \
        --hidden-import PySide6 \
        --hidden-import PySide6.QtCore \
        --hidden-import PySide6.QtGui \
        --hidden-import PySide6.QtWidgets \
        --hidden-import zeroconf \
        --hidden-import psutil \
        --hidden-import yaml \
        --hidden-import rich \
        --hidden-import rich.console \
        --hidden-import rich.table \
        --hidden-import rich.panel \
        --hidden-import rich.layout \
        --hidden-import rich.text \
        --hidden-import rich.live \
        --hidden-import rich.columns \
        "${PROJECT_DIR}/cluster.py" 2>&1 | tail -n 10
}

cmd="${1:-current}"
case "$cmd" in
    current)
        bash "$SCRIPT_DIR/build.sh"
        ;;
    linux|darwin|mingw)
        for arch in $(uname -m); do
            build_one "$cmd" "$arch"
        done
        ;;
    all)
        for platform in linux darwin mingw; do
            build_one "$platform" "$(uname -m)"
        done
        ;;
    *)
        cat <<EOF
Usage: $0 [current|linux|darwin|mingw|all]

  current  Build for the current platform (same as build/build.sh)
  linux    Build for linux x86_64/ARM64
  darwin   Build for macOS x86_64/ARM64 (run on macOS)
  mingw    Build for Windows x86_64 (run on Windows/MinGW)
  all      Build every platform this host supports
EOF
        exit 1
        ;;
esac

echo ""
echo "=== Artifacts ==="
ls -lh "${PROJECT_DIR}/dist/" 2>/dev/null || true
