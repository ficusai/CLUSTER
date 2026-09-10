# OPS — Internal Runbook

> **This file is for operators only.** Replace all `<PLACEHOLDER>` values before deployment.

---

## 1. Inventory (template)

### Root Node
- **Role:** Coordinator + optional local inference
- **OS:** Fedora Workstation
- **RAM:** <TOTAL_RAM_GB> GB
- **Network interface:** Wi-Fi + USB tether (if applicable)

### Worker Nodes
- **Worker 1 (Linux):** `<WORKER1_IP>` | User: `<WORKER1_USER>` | Key: `~/.ssh/<KEY_NAME>`
- **Worker 2 (iPhone):** `<WORKER2_IP>` | User: `root` | Key: `<KEY_NAME>` | USB tunnel: `iproxy`
- **Worker 3 (Android/Termux):** `<WORKER3_IP>`:8022 | User: `u0_a377` | Key: `<KEY_NAME>`

### Storage
- Models: `./legacy/models/*.gguf`
- Binaries: `./legacy/bin/`
- Logs: `./logs/`

---

## 2. Launch

```bash
# Terminal mode
./ai-cluster-events.sh

# Or direct
python3 cluster.py root

# Start worker
python3 cluster.py worker

# Stop
python3 cluster.py stop
# or
./ai-cluster-stop.sh
```

The Desktop launcher (`~/Desktop/ai-cluster.desktop`) runs:

```bash
./launcher-notify.sh --root
```

This shows a notification with **Stop / Restart / Logs** actions handled by `notify-action.py`.

---

## 3. Systemd (Linux)

### System-wide (installed by `install.sh`)

```bash
sudo cp linux/ai-cluster-root.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ai-cluster-root.service
sudo journalctl -u ai-cluster-root.service -f
```

### User services (installed by `install-local.sh`)

```bash
systemctl --user daemon-reload
systemctl --user enable --now ai-cluster-root.service
journalctl --user -u ai-cluster-root.service -f
```

---

## 4. SSH Shortcuts

| Node | Command |
|------|---------|
| Android | `./legacy/ssh-android.sh "tail -f ./legacy/cluster.log"` |
| iPhone (USB) | `./legacy/ssh-iphone.sh --wifi "tail -f ./legacy/cluster.log"` |
| Linux remote | `ssh <WORKER1_USER>@<WORKER1_IP> "journalctl --user -u ai-cluster-worker -f"` |

---

## 5. Troubleshooting

| Symptom | Fix |
|---------|-----|
| Port 8080 refused | Wait 15–20s for model load; check `python3 cluster.py status` |
| Worker missing | Check `rpc-server` process + TCP reachability to root:52053 |
| IP drift | Update `config.yaml` or use Zeroconf/UDP discovery |
| Sandbox/iOS crash | Re-sign: `ldid -S /usr/local/bin/rpc-server` |
| GUI fails to start | Install PySide6: `pip install PySide6` |

---

## 6. Roadmap

- [x] Unified Python launcher with mDNS + UDP discovery
- [x] PySide6 GUI + system tray
- [x] Auto-deployment via SSH (`deploy/deploy-worker.sh`, `cluster.py deploy`)
- [x] Static web dashboard (`dashboard/build/index.html`)
- [x] Desktop notification actions (`launcher-notify.sh` + `notify-action.py`)
- [ ] Task queue + scheduling
- [ ] Production hardening (TLS + auth)
