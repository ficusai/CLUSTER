# AI Cluster Auto-Connect Blueprint

> **How to use:** Humans edit this file to plan refactors; agents use the `ACA-*` codes to locate exact functions/classes in the source. Blueprint mirrors source structure 1:1. Do not edit code files during documentation passes.

> **Layout note (2026-09-19):** Operational shell/Python helpers (`launcher.sh`, `ai-cluster-*.sh`, installers, `notify-action.py`) moved to `scripts/`. PyInstaller `.spec` files moved to `build/`. Guides, audits and reports moved to `docs/`. GGUF models → `models/`, llama.cpp binaries → `bin/`, SSH keys → `security/keys/`, PID/lock state → `runtime/`. File locations in the inventory below remain the original root-level paths; prepend the folder above when resolving.

---

## File Inventory

| Code | File | Purpose |
|------|------|---------|
| `ACA-F01` | `cluster.py` | Main CLI entry; subcommands for root, worker, gui, dashboard, status, logs, stop, build, deploy, clean |
| `ACA-F02` | `launcher.sh` | Bash wrapper used by `.desktop` files and systemd services |
| `ACA-F03` | `launcher-notify.sh` | Desktop notification helper for `--root` mode (legacy; retained for reference) |
| `ACA-F04` | `notify-action.py` | Routes notification action buttons back to `cluster.py` |
| `ACA-F05` | `cluster-dashboard.py` | Standalone Rich TUI dashboard |
| `ACA-F29` | `ai-cluster-desktop-root.sh` | Desktop entry wrapper: starts root in-place and opens the dashboard |
| `ACA-F2A` | `ai-cluster-logs.sh` | Opens the cluster log in a terminal tail view |
| `ACA-F2B` | `assets/ai-cluster.svg` | Desktop/application icon extracted from `src/gui/resources.py` |
| `ACA-F06` | `config.yaml` | Runtime configuration (ports, paths, intervals) |
| `ACA-F07` | `requirements.txt` | Python dependencies |
| `ACA-F08` | `Makefile` | Install/uninstall/test/build/clean targets |
| `ACA-F09` | `AGENTS.md` | AI agent project context |
| `ACA-F0A` | `BLUEPRINT.md` | This file |
| `ACA-F0B` | `src/common/protocol.py` | Wire protocol: `ControlProtocol` |
| `ACA-F0C` | `src/common/discovery.py` | Zeroconf/UDP discovery and advertisement |
| `ACA-F0D` | `src/common/loghub.py` | Central logging hub |
| `ACA-F0E` | `src/common/progress_ui.py` | Rich progress / status UI |
| `ACA-F0F` | `src/root/main.py` | Root node control plane |
| `ACA-F10` | `src/worker/main.py` | Python worker node |
| `ACA-F11` | `src/gui/app.py` | GUI bridge and main entry |
| `ACA-F12` | `src/gui/main_window.py` | PySide6 main window |
| `ACA-F13` | `src/gui/system_tray.py` | System tray icon and menu |
| `ACA-F14` | `src/gui/resources.py` | Compiled icon resources |
| `ACA-F15` | `install.sh` | System-wide installer |
| `ACA-F16` | `install-local.sh` | Per-user installer |
| `ACA-F17` | `deploy/deploy-worker.sh` | Remote Linux worker deployment |
| `ACA-F18` | `dashboard/build/index.html` | Static HTML dashboard |
| `ACA-F19` | `cluster-linux-x86_64.spec` | PyInstaller spec for single-binary build |
| `ACA-F1A` | `linux/launch-cluster.sh` | Helper to start root + worker locally |
| `ACA-F1B` | `linux/connect.sh` | SSH connection helper |
| `ACA-F1C` | `linux/ai-cluster-*.desktop` | Desktop entry templates |
| `ACA-F1D` | `linux/ai-cluster-*.service` | systemd user service templates |
| `ACA-F1E` | `quick-start-cluster.sh` | Quick start helper |
| `ACA-F1F` | `ai-cluster-run.sh` | Runtime wrapper |
| `ACA-F20` | `ai-cluster-stop.sh` | Stop helper |
| `ACA-F21` | `ai-cluster-events.sh` | Event helper |
| `ACA-F22` | `ai-cluster-web.sh` | Web dashboard helper |
| `ACA-F23` | `setup-termux.sh` | Termux bootstrap for Android worker |
| `ACA-F24` | `legacy/start-cluster.sh` | Legacy all-bash one-click start |
| `ACA-F25` | `legacy/start-root.sh` | Legacy root launcher |
| `ACA-F26` | `legacy/start-worker.sh` | Legacy worker launcher |
| `ACA-F27` | `legacy/cluster-supervisor.sh` | Legacy auto-restart watchdog |
| `ACA-F28` | `legacy/cluster-config.env` | Legacy config (no longer used by Gen 2) |
| `ACA-F29` | `legacy/setup-android.sh` | Build llama.cpp rpc-server on Android |
| `ACA-F2A` | `legacy/setup-iphone.sh` | Build llama.cpp rpc-server on jailbroken iPhone |
| `ACA-F2B` | `legacy/setup-usb-tethering.sh` | Fedora USB tethering setup |
| `ACA-F2C` | `legacy/reconnect-android.sh` | Persistent Android SSH reconnect loop |
| `ACA-F2D` | `legacy/ssh-android.sh` / `ssh-iphone.sh` | SSH login helpers |
| `ACA-F2E` | `legacy/termux-boot-script.sh` | Termux:Boot auto-start script |
| `ACA-F2F` | `tests/test_protocol.py` | Protocol tests |
| `ACA-F30` | `tests/test_discovery.py` | Discovery tests |
| `ACA-F31` | `tests/test_worker_exec.py` | Worker execution tests |
| `ACA-F32` | `tests/test_root_fallback.py` | Root fallback tests |
| `ACA-F33` | `tests/conftest.py` | Shared pytest fixtures |

---

## File: `cluster.py` — `ACA-F01`

**Location:** `cluster.py`  
**Role:** Main CLI. Parses arguments, loads `config.yaml`, and dispatches to the correct mode.

### Functions

| Code | Name | Signature | Purpose |
|------|------|-----------|---------|
| `ACA-F01-FN01` | `load_config` | `(path)` | Load and merge `config.yaml` with defaults |
| `ACA-F01-FN02` | `print_banner` | `()` | Print ASCII banner |
| `ACA-F01-FN03` | `choose_mode_interactive` | `()` | Prompt user for mode when none given |
| `ACA-F01-FN04` | `discover_roots_ui` | `(timeout)` | Discover roots on the network and present a menu |
| `ACA-F01-FN05` | `_make_extra_args` | `(args, extra, config)` | Build argv list for launching root/worker subprocesses |
| `ACA-F01-FN06` | `run_as_root` | `(args, ui, config)` | Launch root subprocess via launcher wrapper |
| `ACA-F01-FN07` | `run_as_worker` | `(root_ip, args, ui, config)` | Launch worker subprocess via launcher wrapper |
| `ACA-F01-FN08` | `_launch_gui` | `(mode, args, config)` | Start PySide6 GUI in-process or via subprocess |
| `ACA-F01-FN09` | `_launch_terminal` | `(mode, args, config)` | Start a terminal emulator with the launcher |
| `ACA-F01-FN10` | `check_dependencies` | `()` | Verify Python dependencies are importable |
| `ACA-F01-FN11` | `main` | `()` | CLI entry point |

### CLI Subcommands

| Subcommand | Purpose |
|------------|---------|
| `root` | Start root node |
| `worker` | Start worker node (optionally with `--root-ip`) |
| `gui` | Launch GUI |
| `dashboard` | Launch Rich TUI dashboard |
| `status` | Print cluster status |
| `logs` | Tail root log |
| `stop` | Stop running root/worker processes |
| `build` | Build PyInstaller binary |
| `deploy` | Deploy worker to remote host |
| `clean` | Remove build artifacts and logs |

---

## File: `launcher.sh` — `ACA-F02`

**Location:** `launcher.sh`  
**Role:** Bash wrapper that validates the environment and invokes `cluster.py` with the requested mode.

### Key Sections

| Code | Section | Purpose |
|------|---------|---------|
| `ACA-F02-01` | `set -euo pipefail` | Bash safety |
| `ACA-F02-02` | `PROJECT_DIR` resolution | Resolve script directory |
| `ACA-F02-03` | Python / dependency check | Verify `python3` and required packages |
| `ACA-F02-04` | Mode detection | Detect mode from arg or `.desktop` file name |
| `ACA-F02-05` | `cluster.py` launch | Exec `python3 cluster.py <mode> "$@"` |

---

## File: `launcher-notify.sh` — `ACA-F03`

**Location:** `launcher-notify.sh`  
**Role:** Starts root via `launcher.sh`, then sends a desktop notification with action buttons. Retained for reference; the live Desktop entry now uses `ai-cluster-desktop-root.sh`.

### Key Sections

| Code | Section | Purpose |
|------|---------|---------|
| `ACA-F03-01` | Start root in background | `launcher.sh --root "$@"` |
| `ACA-F03-02` | Capture PID | For lifecycle tracking |
| `ACA-F03-03` | `notify-send` with actions | Buttons: `Stop`, `Restart`, `Logs` |
| `ACA-F03-04` | Start `notify-action.py` | Daemon that listens for action clicks |

---

## File: `ai-cluster-desktop-root.sh` — `ACA-F29`

**Location:** `ai-cluster-desktop-root.sh`  
**Role:** Desktop entry wrapper: stops any stale root process, starts `cluster.py --root --no-ui` in the current terminal, and opens the dashboard once `/api/status` is reachable.

### Key Sections

| Code | Section | Purpose |
|------|---------|---------|
| `ACA-F29-01` | `stop_stale` | Kill existing root / `llama-server` / `rpc-server` processes and release ports |
| `ACA-F29-02` | `open_dashboard` | Poll `http://localhost:8080/api/status`, then `xdg-open` |
| `ACA-F29-03` | Root launch | `exec python3 cluster.py --root --no-ui` |

---

## File: `ai-cluster-logs.sh` — `ACA-F2A`

**Location:** `ai-cluster-logs.sh`  
**Role:** Opens `logs/launcher.log` in a terminal tail view for the Logs desktop action.

### Key Sections

| Code | Section | Purpose |
|------|---------|---------|
| `ACA-F2A-01` | `run_in_terminal` | Try `ptyxis`, `gnome-terminal`, `konsole`, `xfce4-terminal`, `alacritty`, `xterm` |
| `ACA-F2A-02` | Log tail | `tail -n 200 -f logs/launcher.log` |

---

## File: `notify-action.py` — `ACA-F04`

**Location:** `notify-action.py`  
**Role:** Parses notification actions and forwards them to `cluster.py`.

### Functions

| Code | Name | Signature | Purpose |
|------|------|-----------|---------|
| `ACA-F04-FN01` | `_popen_cmd` | `(cmd)` | Run a command without blocking |
| `ACA-F04-FN02` | `main` | `()` | Read action, dispatch to `cluster.py` command |

---

## File: `cluster-dashboard.py` — `ACA-F05`

**Location:** `cluster-dashboard.py`  
**Role:** Standalone Rich-based TUI dashboard.

---

## File: `src/common/protocol.py` — `ACA-F0B`

**Location:** `src/common/protocol.py`  
**Role:** Low-level wire protocol for root/worker communication.

### Functions

| Code | Name | Signature | Purpose |
|------|------|-----------|---------|
| `ACA-F0B-FN01` | `_log_call` | `(source)` | Debug helper |
| `ACA-F0B-FN02` | `make_msg` | `(msg_type)` | Serialize a message dict |
| `ACA-F0B-FN03` | `parse_msg` | `(data)` | Deserialize bytes to message dict |

### Class: `ControlProtocol` — `ACA-F0B-CL01`

| Code | Method | Signature | Purpose |
|------|--------|-----------|---------|
| `ACA-F0B-CL01-M01` | `__init__` | `(self, sock)` | Wrap a socket |
| `ACA-F0B-CL01-M02` | `connect` | `(self, host, port, timeout)` | Connect to remote |
| `ACA-F0B-CL01-M03` | `send` | `(self, msg_type)` | Send a framed message |
| `ACA-F0B-CL01-M04` | `recv` | `(self)` | Receive a framed message |
| `ACA-F0B-CL01-M05` | `close` | `(self)` | Close socket |

---

## File: `src/common/discovery.py` — `ACA-F0C`

**Location:** `src/common/discovery.py`  
**Role:** Zeroconf/mDNS advertisement and discovery, plus UDP broadcast fallback.

### Functions

| Code | Name | Signature | Purpose |
|------|------|-----------|---------|
| `ACA-F0C-FN01` | `_get_local_ip` | `()` | Best-effort local IP detection |
| `ACA-F0C-FN02` | `discover_roots_on_network` | `(timeout)` | Discover roots via mDNS |

### Class: `MDNSAdvertiser` — `ACA-F0C-CL01`

| Code | Method | Purpose |
|------|--------|---------|
| `ACA-F0C-CL01-M01` | `start` | Publish worker service |
| `ACA-F0C-CL01-M02` | `stop` | Unpublish worker service |

### Class: `MDNSDiscovery` — `ACA-F0C-CL02`

| Code | Method | Purpose |
|------|--------|---------|
| `ACA-F0C-CL02-M01` | `start` | Browse for worker services |
| `ACA-F0C-CL02-M02` | `stop` | Stop browsing |

### Class: `UDPBroadcastDiscovery` — `ACA-F0C-CL03`

| Code | Method | Purpose |
|------|--------|---------|
| `ACA-F0C-CL03-M01` | `start_listener` | Listen for UDP broadcasts |
| `ACA-F0C-CL03-M02` | `broadcast` | Send UDP broadcast |
| `ACA-F0C-CL03-M03` | `stop` | Stop listener |

### Class: `MDNSRootAdvertiser` — `ACA-F0C-CL04`

| Code | Method | Purpose |
|------|--------|---------|
| `ACA-F0C-CL04-M01` | `start` | Publish root service |
| `ACA-F0C-CL04-M02` | `stop` | Unpublish root service |

---

## File: `src/common/loghub.py` — `ACA-F0D`

**Location:** `src/common/loghub.py`  
**Role:** Centralized logging with stdout/stderr capture, rotation, and orchestrator notifications.

### Class: `LogWriter` — `ACA-F0D-CL01`

| Code | Method | Purpose |
|------|--------|---------|
| `ACA-F0D-CL01-M01` | `write` | Capture stream write |
| `ACA-F0D-CL01-M02` | `flush` | Flush stream |

### Class: `LogHub` — `ACA-F0D-CL02`

| Code | Method | Purpose |
|------|--------|---------|
| `ACA-F0D-CL02-M01` | `info` | Log INFO |
| `ACA-F0D-CL02-M02` | `warn` | Log WARNING |
| `ACA-F0D-CL02-M03` | `error` | Log ERROR |
| `ACA-F0D-CL02-M04` | `exception` | Log exception trace |
| `ACA-F0D-CL02-M05` | `log_call` | Decorator for function call logging |
| `ACA-F0D-CL02-M06` | `notify_orchestrator` | Send desktop notification |
| `ACA-F0D-CL02-M07` | `stop` | Stop logging hub |

---

## File: `src/common/progress_ui.py` — `ACA-F0E`

**Location:** `src/common/progress_ui.py`  
**Role:** Rich-based progress/status UI shared by CLI and TUI modes.

### Functions

| Code | Name | Signature | Purpose |
|------|------|-----------|---------|
| `ACA-F0E-FN01` | `_detect_notifier` | `()` | Detect available notification backend |
| `ACA-F0E-FN02` | `send_notification` | `(title, message, urgency)` | Send OS notification |

### Class: `ProgressUI` — `ACA-F0E-CL01`

| Code | Method | Purpose |
|------|--------|---------|
| `ACA-F0E-CL01-M01` | `start` | Start UI refresh loop |
| `ACA-F0E-CL01-M02` | `stop` | Stop UI refresh loop |
| `ACA-F0E-CL01-M03` | `set_service` | Update service status |
| `ACA-F0E-CL01-M04` | `add_event` | Append event line |
| `ACA-F0E-CL01-M05` | `update_worker` | Update worker row |
| `ACA-F0E-CL01-M06` | `remove_worker` | Remove worker row |
| `ACA-F0E-CL01-M07` | `set_connection` | Update root connection status |
| `ACA-F0E-CL01-M08` | `notify_once` | Debounced notification |

---

## File: `src/root/main.py` — `ACA-F0F`

**Location:** `src/root/main.py`  
**Role:** Root node control plane: registry, task dispatch, health checks, HTTP API, llama-server management.

### Functions

| Code | Name | Signature | Purpose |
|------|------|-----------|---------|
| `ACA-F0F-FN01` | `detect_cpu_cores` | `()` | CPU core detection |
| `ACA-F0F-FN02` | `detect_ram` | `()` | RAM detection |
| `ACA-F0F-FN03` | `main` | `(ui)` | Root entry point |

### Class: `WorkerRegistry` — `ACA-F0F-CL01`

| Code | Method | Purpose |
|------|--------|---------|
| `ACA-F0F-CL01-M01` | `register` | Add worker |
| `ACA-F0F-CL01-M02` | `unregister` | Remove worker |
| `ACA-F0F-CL01-M03` | `get_active` | List active workers |
| `ACA-F0F-CL01-M04` | `get_worker_count` | Count active workers |
| `ACA-F0F-CL01-M05` | `get_connection` | Get worker socket |
| `ACA-F0F-CL01-M06` | `update_last_seen` | Update heartbeat timestamp |

### Class: `TaskManager` — `ACA-F0F-CL02`

| Code | Method | Purpose |
|------|--------|---------|
| `ACA-F0F-CL02-M01` | `dispatch_task` | Send task to worker and await result |
| `ACA-F0F-CL02-M02` | `record_result` | Store task result |
| `ACA-F0F-CL02-M03` | `get_result` | Retrieve task result |

### Class: `ClusterRoot` — `ACA-F0F-CL03`

| Code | Method | Purpose |
|------|--------|---------|
| `ACA-F0F-CL03-M01` | `start_root_advertising` | Advertise root on mDNS/UDP |
| `ACA-F0F-CL03-M02` | `start_tcp_server` | Accept worker TCP connections |
| `ACA-F0F-CL03-M03` | `start_mdns_discovery` | Discover non-RPC workers via mDNS |
| `ACA-F0F-CL03-M04` | `start_local_rpc` | Start local llama.cpp RPC backend |
| `ACA-F0F-CL03-M05` | `start_llama_server` | Start llama.cpp HTTP server |
| `ACA-F0F-CL03-M06` | `rebuild_llama_server` | Rebuild server on failure |
| `ACA-F0F-CL03-M07` | `start_http_api` | Start root HTTP API + dashboard |
| `ACA-F0F-CL03-M08` | `check_llama_workers` | Health-check llama workers |
| `ACA-F0F-CL03-M09` | `run` | Main async run loop |
| `ACA-F0F-CL03-M10` | `stop` | Graceful shutdown |

---

## File: `src/worker/main.py` — `ACA-F10`

**Location:** `src/worker/main.py`  
**Role:** Python worker that registers with root, receives tasks, and manages local RPC slots.

### Functions

| Code | Name | Signature | Purpose |
|------|------|-----------|---------|
| `ACA-F10-FN01` | `detect_platform` | `()` | Detect OS platform |
| `ACA-F10-FN02` | `detect_cpu_cores` | `()` | CPU cores |
| `ACA-F10-FN03` | `detect_ram` | `()` | RAM info |
| `ACA-F10-FN04` | `_get_local_ip` | `()` | Local IP |
| `ACA-F10-FN05` | `main` | `(ui)` | Worker entry point |

### Class: `ClusterWorker` — `ACA-F10-CL01`

| Code | Method | Purpose |
|------|--------|---------|
| `ACA-F10-CL01-M01` | `start_advertising` | Advertise worker via mDNS |
| `ACA-F10-CL01-M02` | `discover_root` | Find root via Zeroconf or fallback |
| `ACA-F10-CL01-M03` | `register_with_root` | TCP register with root |
| `ACA-F10-CL01-M04` | `handle_connection` | Main connection handler |
| `ACA-F10-CL01-M05` | `_heartbeat` | Send periodic heartbeats |
| `ACA-F10-CL01-M06` | `_handle_message` | Dispatch incoming messages |
| `ACA-F10-CL01-M07` | `_handle_exec` | Execute shell command |
| `ACA-F10-CL01-M08` | `_handle_start_rpc` | Start local RPC backend |
| `ACA-F10-CL01-M09` | `_handle_stop_rpc` | Stop local RPC backend |
| `ACA-F10-CL01-M10` | `_reconnect` | Reconnect on disconnect |
| `ACA-F10-CL01-M11` | `run` | Main async run loop |
| `ACA-F10-CL01-M12` | `stop` | Graceful shutdown |

---

## File: `src/gui/app.py` — `ACA-F11`

**Location:** `src/gui/app.py`  
**Role:** GUI bridge between PySide6 UI and cluster backend.

### Class: `ClusterBridge` — `ACA-F11-CL01`

| Code | Method | Purpose |
|------|--------|---------|
| `ACA-F11-CL01-M01` | `set_cluster` | Attach backend cluster instance |
| `ACA-F11-CL01-M02` | `log` / `notify` | Forward log/notify events |
| `ACA-F11-CL01-M03` | `set_service` / `update_worker` | Forward status updates |
| `ACA-F11-CL01-M04` | `run_cluster` / `stop_cluster` | Start/stop backend in a thread |
| `ACA-F11-CL01-M05` | `get_uptime` | Return uptime string |

### Functions

| Code | Name | Signature | Purpose |
|------|------|-----------|---------|
| `ACA-F11-FN01` | `run_gui` | `(mode, cluster_fn)` | Start QApplication and main window |

---

## File: `src/gui/main_window.py` — `ACA-F12`

**Location:** `src/gui/main_window.py`  
**Role:** PySide6 main window with status, worker table, event log, services, system info.

### Classes

| Code | Class | Purpose |
|------|-------|---------|
| `ACA-F12-CL01` | `StatusIndicator` | Colored status dot |
| `ACA-F12-CL02` | `InfoCard` | Key/value card widget |
| `ACA-F12-CL03` | `WorkerTable` | Worker list table |
| `ACA-F12-CL04` | `EventLog` | Scrollable event log |
| `ACA-F12-CL05` | `ServicesGroup` | Service status widgets |
| `ACA-F12-CL06` | `SystemInfoPanel` | Host system info panel |
| `ACA-F12-CL07` | `MainWindow` | Main application window |

---

## File: `src/gui/system_tray.py` — `ACA-F13`

**Location:** `src/gui/system_tray.py`  
**Role:** System tray icon with dynamic status badge.

### Functions

| Code | Name | Signature | Purpose |
|------|------|-----------|---------|
| `ACA-F13-FN01` | `_make_tray_pixmap` | `(status, badge)` | Render tray pixmap |
| `ACA-F13-FN02` | `get_tray_icon` | `(status, badge)` | Return QIcon |

### Class: `SystemTray` — `ACA-F13-CL01`

| Code | Method | Purpose |
|------|--------|---------|
| `ACA-F13-CL01-M01` | `update_status` | Update icon badge |
| `ACA-F13-CL01-M02` | `show_message` | Show balloon notification |
| `ACA-F13-CL01-M03` | `stop` | Hide tray |

---

## File: `src/gui/resources.py` — `ACA-F14`

**Location:** `src/gui/resources.py`  
**Role:** Compiled PySide6 resource file (icons). Generated; do not hand-edit.

---

## Section: Installers & Deployment

### File: `install.sh` — `ACA-F15`

**Role:** System-wide install: copies files to `/opt/ai-cluster-auto-connect/`, installs systemd services, desktop entries.

### File: `install-local.sh` — `ACA-F16`

**Role:** Per-user install: copies into project directory, installs user systemd services and desktop entries.

### File: `deploy/deploy-worker.sh` — `ACA-F17`

**Role:** Push worker runtime to a remote Linux host over SSH and start it.

---

## Section: Tests

### File: `tests/test_protocol.py` — `ACA-F2F`

**Role:** Unit tests for `src/common/protocol.py` encoding/decoding.

### File: `tests/test_discovery.py` — `ACA-F30`

**Role:** Unit tests for discovery helpers.

### File: `tests/test_worker_exec.py` — `ACA-F31`

**Role:** Unit tests for worker task execution.

### File: `tests/test_root_fallback.py` — `ACA-F32`

**Role:** Unit tests for root fallback logic.

### File: `tests/conftest.py` — `ACA-F33`

**Role:** Shared pytest fixtures.

---

## Default Configuration (`config.yaml`)

| Key | Default | Description |
|-----|---------|-------------|
| `cluster.name` | `"ai-cluster"` | Cluster name |
| `cluster.root_only` | `false` | If true, this device never runs as a worker |
| `network.ctrl_port` | `52053` | TCP control channel (root listens, workers connect) |
| `network.rpc_port` | `50052` | llama.cpp RPC backend port |
| `network.udp_discovery_port` | `52052` | UDP discovery broadcast port |
| `root.http_port` | `8080` | Root HTTP API + dashboard port |
| `ai.model` | path under `models/` | Default GGUF model |
| `ai.threads` | `4` | Default CPU threads for llama-server |
| `ai.context_size` | `4096` | Model context size |
| `ai.n_gpu_layers` | `0` | GPU layers (keep 0 for CPU-only) |
| `workers.deploy_credentials` | per-platform map | SSH user/key/port for remote deploy |

---

## Port Reference

| Port | Used By |
|------|---------|
| `52053` | Root TCP control plane (worker registration, task dispatch, heartbeat) |
| `52052` | UDP discovery broadcast |
| `50052` | llama.cpp RPC backend |
| `8080` | Root HTTP API / dashboard |
| `8081+` | llama-server HTTP API slots (fallback) |
| `8022` | Termux SSH default (Android) |
