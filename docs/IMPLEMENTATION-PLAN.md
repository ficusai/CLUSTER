# AI Cluster Auto-Connect — Implementation Plan

## 1. Project Overview

**Goal:** A cross-platform system where installing a single executable on any device automatically discovers all other devices on the local network and connects them into a distributed computing cluster — with minimal manual configuration.

**Root Node:** The main coordinator. Runs the control plane, HTTP API, and optionally local inference.
**Worker Nodes:** Helper devices that register with the root and contribute CPU/RAM.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│   cluster.py (Unified Launcher)                                │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │ mDNS     │  │ UDP      │  │ HTTP API :8080    │  │
│  │ Discovery│  │ Broadcast│  │ + Worker Registry │  │
│  └────┬────┘  └────┬────┘  └────────┬─────────┘  │
│       │              │                  │               │
│       ▼              ▼                  ▼               │
│  ┌────────────────────────────────────────────────────┐     │
│  │        TCP Control Protocol :52053                         │     │
│  │  (registration, heartbeats, tasks, results)                │     │
│  └────────────────────────────────────────────────────┘     │
└────────────────────────┬───────────────────────────────┘
                       │
     ┌────────────────────────┼─────────────────────────┐
     ▼                  ▼                      ▼
┌──────────┐     ┌──────────┐          ┌──────────┐
│ Helper 1 │     │ Helper 2 │    ...   │ Helper N │
│ (worker) │     │ (worker) │          │ (worker) │
└──────────┘     └──────────┘          └──────────┘
```

### Discovery (Auto-Connect)

All devices discover each other using two parallel methods:

| Method | Protocol | Port | Purpose |
|--------|----------|------|---------|
| **mDNS** | Multicast DNS (zeroconf) | 5353 | Primary: `_cluster-root._tcp` and `_cluster-worker._tcp` |
| **UDP Broadcast** | UDP broadcast | 52052 | Fallback: root announces every 5s, workers listen |

The **root** advertises via both mDNS + UDP.  
The **worker** discovers roots via both mDNS + UDP simultaneously.

### Protocol (over TCP)

Simple JSON-line protocol. Each message is a JSON object terminated by newline.

**Worker → Root (Registration):**
```json
{"type":"register","hostname":"android-phone","platform":"android","arch":"aarch64","cpu_cores":8,"ram_total":7.2,"ram_available":3.0,"rpc_port":50052}
```

### Platform Detection

| Platform | Detection Method |
|----------|-----------------|
| Linux | `platform.system() == "linux"` |
| Android (Termux) | `/data/data/com.termux/files/usr` exists |
| macOS | `platform.system() == "darwin"` |
| Windows | `platform.system() == "windows"` |
| iOS | `platform.platform()` contains "iphone" or "ipad" |

---

## 3. Implementation Status

| Feature | Status |
|---------|--------|
| mDNS service advertisement (zeroconf) | ✅ Optional fallback |
| UDP broadcast discovery | ✅ |
| TCP registration + heartbeat + protocol | ✅ |
| Worker capability reporting (CPU, RAM, platform) | ✅ |
| Root HTTP API for cluster status | ✅ |
| AI cluster mode (llama.cpp RPC) | ✅ Legacy compatible |
| Worker auto-reconnection | ✅ Exponential backoff |
| Graceful fallback without zeroconf | ✅ |
| Graceful fallback without psutil | ✅ |
| Cross-platform: Linux | ✅ Tested (Fedora root + worker) |
| Cross-platform: Windows | ✅ Detection only; onboarding not implemented |
| Cross-platform: Android (Termux) | ✅ Detection + paths + partial SSH onboarding |
| Cross-platform: macOS | ✅ Detection only; onboarding not implemented |
| Cross-platform: iOS | ✅ Detection + on-device build scripts |
| Unified single-binary launcher | ✅ PyInstaller build |
| PySide6 GUI + system tray | ✅ |
| Auto-deployment via SSH | ✅ `deploy/deploy-worker.sh` + `cluster.py deploy` |
| Rich TUI dashboard | ✅ `cluster-dashboard.py` |
| Static web dashboard | ✅ `dashboard/build/index.html` |
| Desktop notification actions | ✅ `launcher-notify.sh` + `notify-action.py` |
| Task queuing / scheduling | 🔄 Basic task dispatch only |
| Production hardening (TLS, auth) | 🔄 Future |

---

## 4. Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run as ROOT device (coordinator):
python3 cluster.py root

# Run as HELPER device (auto-discovers root):
python3 cluster.py worker

# Launch GUI:
python3 cluster.py gui

# Or build a standalone binary:
make build

# Run the built binary:
./dist/cluster-linux-x86_64
```

### Local Test (single device)

```bash
# Terminal 1: Start root
python3 cluster.py root --ctrl-port 52057 --http-port 8083

# Terminal 2: Start worker
python3 cluster.py worker --root-ip 127.0.0.1 --ctrl-port 52057

# Check status:
curl http://localhost:8083/api/status
```

---

## 5. File Structure

```text
ai-cluster-auto-connect/
├── cluster.py                    # UNIFIED ENTRY POINT
├── config.yaml                   # Cluster configuration
├── requirements.txt              # Dependencies
├── Makefile                      # install / uninstall / test / build / clean
├── README.md                     # Project overview
├── scripts/                      # Shell/Python helpers:
│   ├── launcher.sh               # Bash wrapper for .desktop / systemd
│   ├── quick-start-cluster.sh    # Bash quick-start launcher
│   ├── ai-cluster-run.sh         # Runtime wrapper
│   ├── ai-cluster-stop.sh        # Stop script
│   ├── ai-cluster-events.sh      # Live log window helper
│   ├── ai-cluster-web.sh         # Web dashboard helper
│   ├── setup-termux.sh           # Termux bootstrap
│   ├── install.sh                # System-wide installer
│   ├── install-local.sh          # Per-user installer
│   └── notify-action.py          # Notification action dispatcher
├── docs/                         # Guides (ARCHITECTURE, BLUEPRINT, OPS, ...)
├── models/                       # GGUF model weights
├── bin/                          # llama.cpp binaries
├── src/
│   ├── common/
│   │   ├── protocol.py           # JSON-line protocol over TCP
│   │   ├── discovery.py          # mDNS + UDP broadcast discovery
│   │   ├── loghub.py             # Centralized logging
│   │   └── progress_ui.py        # Rich terminal dashboard
│   ├── root/
│   │   └── main.py               # Cluster root coordinator
│   ├── worker/
│   │   └── main.py               # Cluster worker (helper)
│   └── gui/
│       ├── app.py                # GUI bridge
│       ├── main_window.py        # Main PySide6 window
│       ├── system_tray.py        # Tray icon
│       └── resources.py          # Compiled icons
├── build/                        # PyInstaller build scripts
├── deploy/
├── linux/                        # systemd services and desktop entries
├── macos/                        # macOS helper placeholder
├── windows/                      # Windows helper placeholder
├── legacy/                       # Original bash scripts (reference)
├── dashboard/build/index.html    # Static web dashboard
├── dist/                         # PyInstaller build output
└── logs/                         # Rotated session logs
```
