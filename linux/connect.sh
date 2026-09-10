#!/usr/bin/env bash
# AI Cluster Auto-Connect — Linux worker quick-connect
# Run this on a target Linux machine to join the cluster as a worker.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "AI Cluster Auto-Connect — Linux Worker"
echo ""
echo "To join this machine as a worker:"
echo "  1. Ensure Python 3.9+ is installed"
echo "  2. cd ${SCRIPT_DIR}/../.."
echo "  3. python3 src/worker/main.py"
echo ""
echo "The worker will auto-discover the root via mDNS/UDP broadcast."
