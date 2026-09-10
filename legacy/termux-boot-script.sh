#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
# Termux:Boot script — AI Cluster Worker autostart on Android
# Place this at: ~/.termux/boot/start-worker.sh
# Requires: Termux:Boot app from F-Droid
# =============================================================================
# Wait for network
sleep 10

# Kill any existing rpc-server
pkill -f rpc-server 2>/dev/null || true

# Start worker
cd ~/ai-cluster
exec ./start-worker.sh
