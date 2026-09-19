# AI Cluster Auto-Connect — Architecture

## Purpose

Cross-platform distributed AI inference cluster launcher. A Fedora host runs the **root** node (coordinator + OpenAI-compatible HTTP API); Linux/Android/iOS devices run **workers** that contribute CPU/RAM via llama.cpp RPC. Workers auto-discover the root via mDNS/Zeroconf or UDP broadcast fallback.

Two generations coexist:
- **Gen 1** (`legacy/`): Bash-based implementation with hardcoded IPs and pre-built binaries.
- **Gen 2** (`src/`, `cluster.py`): Python asyncio control plane with zero-config discovery, heartbeat health checks, and a PySide6 GUI.

---

## Directory Structure

```
ai-cluster-auto-connect/
├── cluster.py                  # [ENTRY POINT] Unified Python CLI
├── config.yaml                 # Runtime config (ports, model path, credentials)
├── requirements.txt            # Python dependencies
├── Makefile                    # install / uninstall / test / build / clean
├── README.md                   # Project overview
├── scripts/                    # Operational shell/Python helpers (launcher, ai-cluster-*, installers)
├── src/                        # [GEN 2] Python source
│   ├── common/                 # protocol.py, discovery/, loghub/, progress_ui/
│   ├── root/                   # Root coordinator
│   ├── worker/                 # Auto-connect worker
│   └── gui/                    # PySide6 desktop UI
├── build/                      # PyInstaller build scripts + .spec files
├── dist/                       # Build output
├── deploy/                     # Remote worker SSH deployment
├── models/                     # GGUF model weights (gitignored)
├── bin/                        # llama.cpp binaries (llama-server, rpc-server)
├── security/keys/              # SSH keys for remote deploy (gitignored)
├── runtime/                    # PID/lock/state files (gitignored)
├── launchers/                  # User-facing .desktop launchers
├── linux/  macos/  windows/    # Platform helpers + systemd templates
├── docs/                       # Guides, audits, reports
├── logs/                       # Runtime log output (gitignored)
├── tests/                      # pytest suite
├── legacy/                     # [GEN 1] Bash / SSH helpers / setup scripts
└── dashboard/build/index.html  # Static HTML dashboard
```

---

## Module Dependency Graph

```
cluster.py
├── src/common/protocol.py        # Message framing + ControlProtocol
├── src/common/discovery.py       # mDNS + UDP discovery
│   └── (optional) zeroconf
├── src/common/loghub.py          # Central logging hub
├── src/common/progress_ui.py     # Rich dashboard + notifications
│   └── (optional) rich
├── src/root/main.py              # ClusterRoot, WorkerRegistry, TaskManager
│   ├── src/common/protocol.py
│   ├── src/common/discovery.py
│   ├── src/common/loghub.py
│   └── src/common/progress_ui.py
├── src/worker/main.py            # ClusterWorker, auto-discovery, registration
│   ├── src/common/protocol.py
│   ├── src/common/discovery.py
│   ├── src/common/loghub.py
│   └── src/common/progress_ui.py
└── src/gui/app.py                # ClusterBridge + run_gui
    ├── src/common/progress_ui.py
    ├── src/gui/main_window.py
    └── src/gui/system_tray.py
```

---

## Data Flow

### Worker Startup
1. `cluster.py worker` → `ClusterWorker.run()`
2. `discover_root()` uses mDNS/Zeroconf or UDP broadcast to find root
3. `register_with_root(root_ip)` opens TCP to `root_ip:ctrl_port` (default 52053)
4. Sends `register` JSON (hostname, platform, arch, cores, RAM, rpc_port)
5. Root replies `register_ack` with worker_id
6. Worker starts `_read_loop()` and `_heartbeat()` every heartbeat interval
7. If `ai_mode` is enabled, root sends `start_rpc` and worker launches local `rpc-server`

### Root Startup
1. `cluster.py root` → `ClusterRoot.run()`
2. Starts local `rpc-server` if `ai_mode` is enabled
3. Starts mDNS discovery (browses `_cluster-worker._tcp`)
4. Starts mDNS root advertising (`_cluster-root._tcp`)
5. Starts UDP broadcast announcer on `udp_discovery_port` (default 52052) every 5s
6. Starts TCP control server on `ctrl_port` (default 52053)
7. Starts HTTP API on `http_port` (default 8080) and serves `dashboard/build/index.html`
8. Starts `llama-server` with `--rpc` pointing to all discovered workers
9. Background task `check_llama_workers()` monitors topology and restarts llama-server when workers change

### Runtime Protocol (TCP control channel)
```
Worker ──[register]──▶ Root
Root   ──[register_ack]──▶ Worker
Worker ──[ping]──▶ Root      (heartbeat)
Root   ──[pong]──▶ Worker
Root   ──[task]──▶ Worker   (exec, start_rpc, stop_rpc)
Worker ──[result]──▶ Root
Worker ──[disconnect]──▶ Root
```

### HTTP API (root port 8080)
```
GET  /api/status        → cluster state + worker list
GET  /api/workers       → registered workers
GET  /api/tasks?id=X    → task result
POST /api/task/exec     → dispatch command to worker(s)
POST /api/rebuild       → restart llama-server
POST /api/stop          → graceful shutdown
```

### LLM Inference (AI mode)
```
Client ──▶ root:8080/v1/chat/completions
  ├── llama-server on root
  ├── Model split via --rpc:
  │   ├── 127.0.0.1:50052       (root local)
  │   ├── <worker-ip>:50052   (Android / iPhone / remote worker)
  │   └── ...
  └── Each rpc-server handles a shard of layers
```

---

## Key Classes

| Class | File | Role |
|-------|------|------|
| `ControlProtocol` | `src/common/protocol.py` | TCP socket wrapper (connect/send/recv/close) |
| `MDNSAdvertiser` | `src/common/discovery.py` | Worker advertises `_cluster-worker._tcp` |
| `MDNSRootAdvertiser` | `src/common/discovery.py` | Root advertises `_cluster-root._tcp` |
| `MDNSDiscovery` | `src/common/discovery.py` | Browse for worker services |
| `UDPBroadcastDiscovery` | `src/common/discovery.py` | UDP broadcast listener/sender |
| `LogHub` | `src/common/loghub.py` | Centralized logging + stdout/stderr capture |
| `ProgressUI` | `src/common/progress_ui.py` | Rich live dashboard + OS notifications |
| `WorkerRegistry` | `src/root/main.py` | Thread-safe worker tracking + heartbeat timeout |
| `TaskManager` | `src/root/main.py` | Dispatch tasks and collect results |
| `ClusterRoot` | `src/root/main.py` | Orchestrator: TCP server, HTTP API, llama.cpp manager |
| `ClusterWorker` | `src/worker/main.py` | Auto-discover, register, heartbeats, task handlers |
| `ClusterBridge` | `src/gui/app.py` | Bridge between GUI and cluster backend |
| `MainWindow` | `src/gui/main_window.py` | PySide6 main window |
| `SystemTray` | `src/gui/system_tray.py` | Tray icon with dynamic status badge |

---

## Configuration

- **`config.yaml`** — Gen 2 runtime config: cluster name, ports, model path, credentials per platform.
- **`legacy/cluster-config.env`** — Gen 1 hardcoded IPs. No longer sourced by Gen 2 code; retained for legacy scripts.
- **CLI flags** override config: `--port`, `--rpc-port`, `--http-port`, `--root-ip`, `--model`, `--ai-mode`.
- **Env vars** for Gen 1 workers: `ROOT_IP`, `RPC_PORT`, `THREADS`.

---

## Build & Deploy

- From source: `python3 cluster.py root` / `python3 cluster.py worker` / `python3 cluster.py gui`
- Bash wrapper: `./scripts/launcher.sh root`
- Single binary: `make build` → `dist/cluster-linux-x86_64`
- Cross-platform: `./build/build-all.sh` (linux x86_64/ARM64, macOS x86_64/ARM64, Windows x86_64)
- Deploy worker: `python3 cluster.py deploy user@host` or `deploy/deploy-worker.sh`
- Auto-start: systemd (Linux), Termux:Boot (Android), LaunchDaemon (macOS/iOS, manual)

---

## Ports

| Port | Service | Protocol |
|------|---------|----------|
| 52053 | Root TCP control plane (worker registration, task dispatch, heartbeat) | TCP |
| 52052 | UDP discovery broadcast | UDP |
| 50052 | llama.cpp RPC backend | TCP |
| 8080 | Root HTTP API + dashboard | TCP |
| 8081+ | llama-server HTTP API slots (fallback) | TCP |
| 8022 | Termux SSH (Android) | TCP |
