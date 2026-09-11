# AI Cluster Auto-Connect

**Version:** 1.3.0  
**Status:** Active development; Gen-2 Python control plane optimized for cross-platform Linux distributions (Fedora, Debian/Ubuntu, Arch, Alpine, Termux, Android).  
**License:** MIT

---

## What it is

A cross-platform launcher for distributed AI inference using llama.cpp RPC. One device becomes the **root** (coordinator + HTTP API + Web Dashboard); any number of devices become **workers** (CPU/RAM donors). Workers auto-discover the root via mDNS/Zeroconf or fall back to UDP broadcast — no manual IP configuration required on the same broadcast domain.

Primary platform: **Linux** for the root coordinator and workers. Heterogeneous workers are supported across x86_64, ARM64, Android (Termux), and mobile devices running the upstream `llama.cpp` `rpc-server` binary directly.

---

## Supported Operating Systems

| Operating System | Supported |
| :--- | :---: |
| LINUX | ✅ |
| WINDOWS | ✅ |
| MACOS | ✅ |
| ANDROID | ✅ |
| IOS | ❌ |

---

## Quick Start

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start root device
python3 cluster.py root

# Start worker node from another machine
python3 cluster.py worker

# Launch PySide6 GUI (optional)
python3 cluster.py gui
```

---

## Installation

### Non-Root / User-Space Installation (Recommended)

```bash
# Install binary & desktop launcher to ~/.local/bin and ~/.local/share/applications
make install-local
# or
./install-local.sh
```

### System-Wide Installation (Root / Sudo)

```bash
# Install binary to /usr/local/bin and systemd services to /etc/systemd/system
make install
```

---

## Key Features & Optimizations

- **Zero-Config Root Discovery:** Dual-track mDNS/Zeroconf + UDP broadcast fallback with offline LAN IP resolution (works without internet routing).
- **Dynamic Port Collision Probing:** Automatic port fallback for HTTP API (8080+) and llama-server (8081+) if default ports are occupied.
- **Process Tree & Signal Safety:** Process-group level SIGTERM/SIGKILL termination (`start_new_session=True`) ensures no orphan `llama-server` or `rpc-server` processes are left running.
- **Universal Linux & Non-Root Portability:** Supports both systemd and non-systemd init systems (OpenRC, runit, dinit), custom `PREFIX` user-space installs (`~/.local`), and POSIX shell compatibility.
- **Heterogeneous Architecture Support:** Native execution across x86_64 and ARM64 nodes.
- **Single Binary Releases:** PyInstaller support for standalone root, worker, and combined executables (`make build`).

---

## Project Layout

```
CLUSTER/
├── cluster.py                  # Unified CLI entry point
├── launcher.sh                 # Portable bash wrapper used by .desktop/systemd
├── launcher-notify.sh          # Desktop notification helper for root
├── notify-action.py            # Notification action dispatcher
├── cluster-dashboard.py        # Standalone Rich TUI dashboard
├── config.yaml                 # Cluster-wide configuration
├── requirements.txt            # Python dependencies with minimum bounds
├── Makefile                    # install / install-local / test / build / clean
├── README.md                   # This file
├── AGENTS.md                   # AI agent project context
├── BLUEPRINT.md                # Editable project map with ACA-* codes
├── INSTALLATION.md             # Deployment & multi-distro guide
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
│   ├── common/                 # Protocol, discovery, loghub, progress_ui
│   ├── root/                   # Coordinator
│   ├── worker/                 # Auto-connect worker
│   └── gui/                    # PySide6 GUI + system tray
├── build/                      # PyInstaller build scripts
├── deploy/                     # SSH deployment helper
├── linux/                      # systemd services + desktop entry templates
├── tests/                      # pytest suite
└── dist/                       # PyInstaller build output
```

---

## Network Ports

| Port | Service | Description |
|------|---------|-------------|
| 52053 | Root TCP | Control plane (worker registration, task dispatch, heartbeat) |
| 52052 | UDP Broadcast | Auto-discovery listener & announcer |
| 50052 | RPC Backend | llama.cpp RPC server default port |
| 8080+ | Root HTTP API | Web dashboard & control REST API (auto-probes 8080, 8081...) |
| 8081+ | llama-server | LLaMA HTTP API slots (auto-fallback if port busy) |

---

## Documentation

| File | Purpose |
|------|---------|
| `README.md` | Overview, installation, and quick start |
| `INSTALLATION.md` | Linux distros, non-root installation, systemd & desktop integration |
| `ARCHITECTURE.md` | Data flow, ports, class reference |
| `BLUEPRINT.md` | Editable project map with ACA-* codes |
| `IMPLEMENTATION-PLAN.md` | Feature status and roadmap |
| `OPS.md` | Internal runbook & operations |
| `AGENTS.md` | AI agent project context |

---

## Security

- `/api/task/exec` allows remote task execution on connected workers. Configure `security.api_token` in `config.yaml` or set `AI_CLUSTER_API_TOKEN` env variable when deploying on non-isolated networks.
- All secrets, token keys, and private infrastructure details are sanitized prior to public deployment.
- Process tree cleanups use isolated session groups to prevent terminating unrelated host processes.

---

## Build & Test

```bash
# Run test suite
pytest tests/

# Run system robustness verification
python3 verify_ai_cluster_robustness.py

# Build single binaries via PyInstaller
make build

# Install to user home directory ~/.local/bin
make install-local
```

---

## Support & Troubleshooting

- **Logs:** Verbose rotated session logs are preserved under `logs/`.
- **Port Conflicts:** HTTP API and LLaMA server automatically attempt fallback ports. Check `http://localhost:8080/api/status` for active ports.
- **Firewall:** Ensure local network firewalls permit TCP `52053`, `8080` and UDP `52052`.
