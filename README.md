# AI Cluster Auto-Connect

**Version:** 1.3.0  
**Status:** Active development; Gen-2 Python control plane in daily use on Fedora + Android.  
**License:** MIT

---

## What it is

A cross-platform launcher for distributed AI inference using llama.cpp RPC. One device becomes the **root** (coordinator + HTTP API); any number of devices become **workers** (CPU/RAM donors). Workers auto-discover the root via mDNS/Zeroconf or fall back to UDP broadcast — no manual IP configuration required on the same broadcast domain.

Primary platform: **Linux (Fedora)** for the root node. Python workers run on Linux. Android (Termux) and jailbroken iPhone workers run the upstream llama.cpp `rpc-server` binary directly.

---

## Setup

```bash
# Python deps + test deps
pip install -r requirements.txt

# Start root device
python3 cluster.py root

# Start worker from same directory
python3 cluster.py worker

# Launch GUI
python3 cluster.py gui
```

---

## Quick start

```bash
# Run interactively (prompts for mode)
python3 cluster.py

# Or use the bash wrapper
./launcher.sh root
./launcher.sh worker
./launcher.sh gui

# Build a single binary
python3 cluster.py build
# or
make build
```

---

## Features

- Zero-config root discovery (mDNS/Zeroconf + UDP broadcast fallback)
- Heterogeneous nodes (x86_64 + ARM64 mixed)
- Python asyncio control plane with worker registry and heartbeat health checks
- Single binary via PyInstaller (`cluster-linux-x86_64.spec`)
- Desktop GUI (optional, PySide6) + system tray
- Cross-platform SSH deployment helper (`deploy/deploy-worker.sh`)
- Auto-restart of root-side `llama-server` on port fallback (8081+)

---

## Project layout

```
ai-cluster-auto-connect/
├── cluster.py                  # Unified CLI entry point
├── launcher.sh                 # Bash wrapper used by .desktop/systemd
├── launcher-notify.sh          # Desktop notification helper for root
├── notify-action.py            # Notification action dispatcher
├── cluster-dashboard.py        # Standalone Rich TUI dashboard
├── config.yaml                 # Cluster-wide configuration
├── requirements.txt            # Python dependencies
├── Makefile                    # install / uninstall / test / build / clean
├── README.md                   # This file
├── AGENTS.md                   # AI agent project context
├── BLUEPRINT.md                # Editable project map with ACA-* codes
├── INSTALLATION.md             # Deployment guide
├── ARCHITECTURE.md             # Data flow, ports, class reference
├── IMPLEMENTATION-PLAN.md      # Feature status and roadmap
├── OPS.md                      # Internal runbook
├── quick-start-cluster.sh      # Interactive launcher
├── ai-cluster-run.sh           # Runtime wrapper
├── ai-cluster-stop.sh          # Graceful shutdown helper
├── ai-cluster-events.sh        # Live log window helper
├── ai-cluster-web.sh           # Web dashboard helper
├── setup-termux.sh             # Termux bootstrap for Android
├── src/
│   ├── common/                   # protocol, discovery, loghub, progress_ui
│   ├── root/                     # Coordinator
│   ├── worker/                   # Auto-connect worker
│   └── gui/                      # PySide6 GUI + system tray
├── build/                      # PyInstaller build scripts
├── deploy/                     # SSH deployment helper
├── linux/                      # systemd services + desktop entry templates
├── tests/                      # pytest suite
├── legacy/                     # Gen-1 bash / binaries / model files
├── dashboard/build/index.html  # Static HTML dashboard
└── dist/                       # Build output
```

---

## Ports

| Port | Service |
|------|---------|
| 52053 | Root TCP control plane (worker registration, task dispatch, heartbeat) |
| 52052 | UDP discovery broadcast |
| 50052 | llama.cpp RPC backend |
| 8080 | Root HTTP API + dashboard |
| 8081+ | llama-server HTTP API slots (auto-fallback if 8081 busy) |
| 8022 | Termux SSH default (Android) |

---

## Documentation

| File | Purpose |
|------|---------|
| `README.md` | Overview and quick start |
| `AGENTS.md` | AI agent project context |
| `BLUEPRINT.md` | Editable project map with ACA-* codes |
| `INSTALLATION.md` | Linux, macOS, Windows, systemd notes |
| `ARCHITECTURE.md` | Data flow, ports, class reference |
| `IMPLEMENTATION-PLAN.md` | Feature status and roadmap |
| `OPS.md` | Internal runbook |

---

## Troubleshooting

- **Port 8081 already in use (llama-server won’t start)**  
  The root node auto-falls back to 8082/8083/... and updates `/api/status` URLs accordingly. If issues persist, stop the old `llama-server` process and restart.

- **Orphan processes after stop**  
  The root process kills its spawned process tree for `rpc-server` and `llama-server`. If leftovers remain, run `python3 cluster.py stop` or kill them manually.

- **No workers discovered**  
  Zeroconf/mDNS is optional; UDP broadcast works without it. Ensure devices are on the same broadcast domain and firewall allows TCP 52052/52053 and UDP 52052.

- **Desktop launcher always opens a terminal**  
  This is expected for direct invocation. For background/system-tray launch, use the systemd units under `linux/` instead.

---

## Security

- `/api/task/exec` endpoints allow remote command execution on workers from LAN devices. Harden with authentication before exposing beyond trusted networks.
- `cluster.py worker` auto-discovers root devices; restrict to managed networks.
- Legacy SSH keys live under `legacy/`; add them to `~/.ssh/config` with restricted permissions (`600`).

---

## Build

```bash
make build          # current platform via PyInstaller
make run            # run from source (interactive)
make run-root       # run as root
make run-worker     # run as worker
make clean          # remove build artifacts
```

---

## Support

- Docs: `INSTALLATION.md`, `ARCHITECTURE.md`, `OPS.md`
- Issues: log output is verbose by design; `logs/` contains rotated session logs.
- Tests: `pytest` from the project root.
