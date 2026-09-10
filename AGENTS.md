# AI Cluster Auto-Connect

Distributed AI inference cluster using llama.cpp RPC mode across heterogeneous nodes. A Fedora host acts as the root node; Android (Termux) and iPhone (jailbreak) devices act as RPC workers. A Python 3 asyncio control plane handles node discovery, health checks, task dispatch, and automatic recovery. Optional PySide6 GUI and system-tray integration are included.

## Entry Points

| File | Purpose |
|------|---------|
| `cluster.py` | Main orchestrator CLI: root, worker, gui, dashboard, status, logs, build/deploy helpers |
| `launcher.sh` | Bash wrapper that validates Python, picks a mode (root/gui/deploy), and routes to `cluster.py` |
| `launcher-notify.sh` | GNOME/KDE notification helper (legacy; retained for reference) |
| `ai-cluster-desktop-root.sh` | Desktop entry wrapper: starts root in-place and opens the dashboard |
| `ai-cluster-logs.sh` | Opens the cluster log in a terminal tail view (used by the Logs desktop action) |
| `notify-action.py` | Parses notification actions and routes commands back to `cluster.py` |
| `cluster-dashboard.py` | Minimal TUI dashboard using Rich (legacy but still functional) |

## What It Does

1. **Root node** — Runs an asyncio gRPC-like control plane on port `52053`. Accepts worker registrations, distributes inference slots, exposes `/api/status` on `8080`, and serves a small HTML dashboard from `dashboard/build/`.
2. **Worker node** — Linux Python worker registers with root and forwards llama.cpp RPC traffic, or Android/iPhone workers run the upstream `rpc-server` binary directly.
3. **Discovery** — Uses Zeroconf to advertise/find root nodes on the local network.
4. **Health & healing** — Root pings workers; offline workers are removed. Worker can auto-restart on disconnect.
5. **GUI** — PySide6 app with system tray for launching root, monitoring status, and opening the dashboard.
6. **Deployment** — `deploy-worker.sh` pushes a pre-built PyInstaller worker binary to remote Linux hosts over SSH; Android onboarding uses Termux/SSH.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Fedora host (root + optional GUI)                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ cluster.py  │  │ src/root/   │  │ src/gui/app.py          │  │
│  │  (CLI)      │──│ main.py     │  │  PySide6 + system tray  │  │
│  │  launcher.sh │  │  Control    │  └─────────────────────────┘  │
│  └─────────────┘  │  plane      │           │                   │
│       │           │  port 52053 │           │                   │
│       │           └──────┬──────┘           │                   │
│       │                  │                  ▼                   │
│       ▼                  ▼           dashboard/build/index.html  │
│  launcher-notify.sh  src/common/           (HTTP 8080)              │
│  (root notification) protocol.py                                    │
│                   discovery.py  ◄── Zeroconf (mDNS)                │
│                   loghub.py     ◄── UDP broadcast (52052)          │
└───────────────────┬─────────────────────────────────────────────┘
                    │  TCP control channel (52053)
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────────┐
   │ worker  │ │ worker  │ │ Android/    │
   │ (Fedora)│ │ (Fedora)│ │ iPhone RPC  │
   │ 50052   │ │ 50052   │ │ binary      │
   └─────────┘ └─────────┘ └─────────────┘
```

## File Structure

### `~/ai-cluster/` — Project root

| Path | Role |
|------|------|
| `cluster.py` | Main CLI entry; subcommands: `root`, `worker`, `gui`, `dashboard`, `status`, `logs`, `stop`, `build`, `deploy`, `clean` |
| `launcher.sh` | Bash wrapper; used by `.desktop` files and systemd services |
| `launcher-notify.sh` | Sends desktop notification with action buttons after starting root |
| `ai-cluster-desktop-root.sh` | Desktop entry wrapper: starts root in-place and opens the dashboard |
| `ai-cluster-logs.sh` | Opens the cluster log in a terminal tail view (used by the Logs desktop action) |
| `ai-cluster-stop.sh` | Stops root, worker, and llama.cpp processes |
| `notify-action.py` | Receives notification actions and invokes `cluster.py` commands |
| `cluster-dashboard.py` | Standalone Rich TUI dashboard |
| `config.yaml` | Runtime configuration for root/worker: ports, model path, heartbeat intervals |
| `requirements.txt` | Python dependencies |
| `Makefile` | Convenience targets: `install`, `uninstall`, `install-local`, `test`, `build`, `clean` |
| `AGENTS.md` | This file — AI agent project context |
| `BLUEPRINT.md` | Editable project map with `ACA-*` codes |
| `README.md` | User-facing overview |
| `ARCHITECTURE.md` | Design docs and module relationships |
| `INSTALLATION.md` | Setup instructions |
| `OPS.md` | Day-to-day operations |
| `IMPLEMENTATION-PLAN.md` | Roadmap and status |
| `CHANGELOG.md` | Release history |

### `~/ai-cluster/src/` — Source

| Path | Role |
|------|------|
| `src/common/protocol.py` | Wire protocol: `Message`, `Frame`, `RPCClient`, `RPCServer`, codecs |
| `src/common/discovery.py` | Zeroconf root discovery (`RootDiscovery` + `RootAnnouncer`) |
| `src/common/loghub.py` | Shared logging hub used by root/worker |
| `src/common/progress_ui.py` | Rich-based progress UI for long-running tasks |
| `src/root/main.py` | Root node control plane: worker registry, health, task dispatch, HTTP API |
| `src/worker/main.py` | Python worker: registers with root, manages local slots, heartbeat |
| `src/gui/app.py` | PySide6 GUI entry |
| `src/gui/main_window.py` | Main GUI window |
| `src/gui/system_tray.py` | System tray icon and menu |
| `src/gui/resources.py` | Bundled icon resources |

### `~/ai-cluster/linux/` — Linux desktop/systemd integration

| Path | Role |
|------|------|
| `ai-cluster-root.desktop` | Desktop entry template for root mode |
| `ai-cluster-worker.desktop` | Desktop entry template for worker mode |
| `ai-cluster-gui.desktop` | Desktop entry template for GUI mode |
| `ai-cluster-root.service` | systemd user service template for root |
| `ai-cluster-worker.service` | systemd user service template for worker |
| `ai-cluster-gui.service` | systemd user service template for GUI |
| `launch-cluster.sh` | Helper script to start root + worker locally |
| `connect.sh` | SSH connection helper |

### `~/ai-cluster/legacy/` — First-generation bash implementation

| Path | Role |
|------|------|
| `start-cluster.sh` | Legacy all-bash one-click start |
| `start-root.sh` | Legacy root launcher |
| `start-worker.sh` | Legacy worker launcher |
| `cluster-supervisor.sh` | Legacy auto-restart watchdog |
| `cluster-config.env` | Legacy configuration (no longer sourced by current code) |
| `setup-android.sh` / `setup-iphone.sh` | Build llama.cpp rpc-server on-device |
| `setup-usb-tethering.sh` | Fedora USB tethering helper |
| `reconnect-android.sh` / `ssh-android.sh` / `ssh-iphone.sh` | SSH helpers |
| `termux-boot-script.sh` | Termux:Boot worker auto-start |
| `bin/` | Pre-built `llama-server` and `rpc-server` binaries, plus `.gguf` models |
| `models/` | Bundled GGUF models (TinyLlama, Qwen2.5) |

### `~/ai-cluster/dashboard/` — Web dashboard

| Path | Role |
|------|------|
| `dashboard/build/index.html` | Static dashboard that polls `/api/status` every 3 seconds |

### `~/ai-cluster/deploy/` — Remote deployment

| Path | Role |
|------|------|
| `deploy-worker.sh` | Push pre-built PyInstaller worker binary to a remote Linux host over SSH and start it |

### `~/ai-cluster/tests/` — Unit tests

| Path | Role |
|------|------|
| `tests/test_protocol.py` | Protocol encoding/decoding tests |
| `tests/test_discovery.py` | Zeroconf discovery tests |
| `tests/test_worker_exec.py` | Worker execution tests |
| `tests/test_root_fallback.py` | Root fallback logic tests |
| `tests/conftest.py` | Shared pytest fixtures |

## Default Ports

| Port | Service |
|------|---------|
| `52053` | Root TCP control plane (worker registration, task dispatch, heartbeat) |
| `52052` | UDP discovery broadcast |
| `50052` | llama.cpp RPC backend |
| `8080` | Root HTTP API + dashboard |
| `8081+` | llama-server HTTP API slots (fallback) |
| `8022` | Termux SSH default (Android) |

## Hard Rules

### 1. Do Not Modify Code Files in Documentation Passes
When updating docs, never edit `.py`, `.sh`, `.service`, `.desktop`, `.yaml`, `.spec`, or binary files. Docs must describe the code as-is.

### 2. One Source of Truth for Launcher Paths
The live Desktop file is `~/Desktop/ai-cluster.desktop`. It runs `~/ai-cluster/ai-cluster-desktop-root.sh`. The version-controlled templates live in `linux/`. Installers copy templates into `~/.local/share/applications/` and onto the Desktop.

### 3. Root vs. Legacy
Current control plane is Generation 2 (Python in `src/`). Legacy bash scripts in `legacy/` still exist for reference, Android/iPhone build helpers, and USB tethering setup, but the main orchestrator is `cluster.py`.

### 4. Logging
All Python modules use `src/common/loghub.py`. Do not introduce ad-hoc `print` or `console.log` logging in new code.

### 5. Cross-Platform Onboarding Status
- Linux worker: automated via `deploy-worker.sh` (requires a pre-built PyInstaller binary from `cluster.py build`).
- Android worker: partially automated via Termux + SSH; `setup-termux.sh` bootstraps the device, `setup-android.sh` builds the RPC binary.
- iPhone worker: manual SSH/on-device build via `setup-iphone.sh`.
- Windows/macOS clients: detection exists in scripts, but automated onboarding is not implemented.

## CLI Usage

```bash
# Run the root node
python3 cluster.py root

# Run a worker (auto-discovers root via Zeroconf or falls back to config.yaml)
python3 cluster.py worker

# Launch the GUI
python3 cluster.py gui

# Open the TUI dashboard
python3 cluster.py dashboard

# Show cluster status
python3 cluster.py status

# Follow logs
python3 cluster.py logs

# Stop root/worker services
python3 cluster.py stop

# Build a PyInstaller binary
python3 cluster.py build

# Deploy worker to a remote host
python3 cluster.py deploy user@host

# Clean build artifacts and logs
python3 cluster.py clean
```

## Desktop / Systemd Integration

| Target | Command |
|--------|---------|
| Desktop launcher | `~/Desktop/ai-cluster.desktop` → `ai-cluster-desktop-root.sh` |
| Root service | `systemctl --user start ai-cluster-root.service` |
| Worker service | `systemctl --user start ai-cluster-worker.service` |
| GUI service | `systemctl --user start ai-cluster-gui.service` |
| View logs | `journalctl --user -u ai-cluster-root.service -f` |

## Dependencies

| Dependency | Purpose |
|------------|---------|
| `PySide6` | GUI and system tray |
| `zeroconf` | Network discovery |
| `psutil` | Process/system monitoring |
| `pyyaml` | `config.yaml` parsing |
| `rich` | TUI dashboards and progress UI |
| `grpcio` / `protobuf` (optional) | Future gRPC backend |
| `pyinstaller` (optional) | Binary builds |

## Security Notes

- No credentials are stored in version-controlled files.
- SSH keys for Android are kept in `legacy/android_ssh_key*` and are deployment artifacts, not secrets in docs.
- Replace any accidentally discovered secrets with `[REDACTED]` in documentation.
