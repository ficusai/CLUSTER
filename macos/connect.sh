#!/usr/bin/env zsh
# AI Cluster Auto-Connect — macOS worker quick-connect
# Run this on a target macOS machine to join the cluster as a worker.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "AI Cluster Auto-Connect — macOS Worker"
echo ""
echo "To join this machine as a worker:"
echo "  1. Ensure Python 3.9+ is installed (brew install python@3)"
echo "  2. cd ${SCRIPT_DIR}/../.."
echo "  3. python3 src/worker/main.py"
echo ""
echo "The worker will auto-discover the root via mDNS/UDP broadcast."
