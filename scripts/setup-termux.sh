#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
# Termux Bootstrap for AI Cluster Worker
# This script is meant to be run ONCE inside Termux to prepare the device as a
# cluster worker node. After this, the Fedora host will manage the device via SSH.
# =============================================================================
set -euo pipefail

echo "[Termux] AI Cluster Worker Bootstrap"
echo "[Termux] User: $(whoami)  Home: $HOME"

# 1. Update packages and install deps
echo "[Termux] Installing dependencies..."
pkg update -y
pkg install -y python git openssh

# 2. Python deps (minimal set for worker mode; no GUI needed)
echo "[Termux] Installing Python packages..."
pip install --upgrade pip
pip install pyyaml zeroconf psutil rich

# 3. Storage access (needed if we later need to exchange files via shared storage)
#    termux-setup-storage is interactive on first run; ignore failure in case
#    permissions are already granted.
termux-setup-storage || true

# 4. Prepare SSH directory (Fedora will push authorized_keys)
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

# 5. Enable SSH daemon auto-start on boot (requires Termux:Boot app)
mkdir -p "$HOME/.termux/boot" 2>/dev/null || true
cat > "$HOME/.termux/boot/ai-cluster-sshd" << 'BOOT'
#!/data/data/com.termux/files/usr/bin/bash
# Termux:Boot — restart sshd on boot so Fedora can reconnect without manual input
pkill sshd 2>/dev/null || true
sleep 5
sshd
BOOT
chmod +x "$HOME/.termux/boot/ai-cluster-sshd" || true

# 6. Start sshd now
echo "[Termux] Starting SSH daemon on port 8022..."
pkill sshd 2>/dev/null || true
sshd || true

# 7. Show status
sleep 1
if netstat -tlnp 2>/dev/null | grep -q ':8022'; then
    echo "[Termux] SSH is listening on port 8022."
elif (echo > /dev/tcp/127.0.0.1/8022) 2>/dev/null; then
    echo "[Termux] SSH is listening on port 8022."
else
    echo "[WARN][Termux] Could not verify sshd is running on port 8022."
    echo "  Run 'sshd' manually inside Termux to start it."
fi

echo "[Termux] Bootstrap complete."
echo "  Next step: return to Fedora; the launcher will connect via SSH."
