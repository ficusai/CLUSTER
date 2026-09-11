# CLUSTER — Distributed AI Inference Cluster & Orchestration Engine

> **CLUSTER** is a cross-platform launcher and control plane for distributed AI model inference using `llama.cpp` RPC. It allows multiple computers, Android phones (via Termux), and edge devices to pool their CPU and RAM resources into a unified local AI cluster without requiring complex manual network configuration.

---

## 📖 Table of Contents
- [Overview & Purpose](#-overview--purpose)
- [Key Features](#-key-features)
- [Architecture & Core Concepts](#-architecture--core-concepts)
- [File & Directory Structure](#-file--directory-structure)
- [Installation & Setup](#-installation--setup)
- [Usage Guide (CLI & GUI)](#-usage-guide-cli--gui)
- [Testing & Quality Verification](#-testing--quality-verification)
- [Git & Release Branching](#-git--release-branching)
- [License & Attribution](#-license--attribution)

---

## 💡 Overview & Purpose

Modern Large Language Models (LLMs) often exceed the memory or compute capacity of a single machine. **CLUSTER** solves this by connecting a primary **Root Coordinator** node with any number of **Worker** nodes across local networks. 

* The **Root Node** handles overall task orchestration, model loading parameters, an OpenAI-compatible REST API server, and a live web dashboard.
* The **Worker Nodes** run computational compute processes (`llama.cpp` `rpc-server`) to process model layers offloaded across the network.

Whether running on Linux distributions (Fedora, Debian, Ubuntu, Arch), macOS, Windows, or Android devices, CLUSTER automatically connects devices via local network zero-configuration discovery.

---

## ⚡ Key Features

* **Zero-Configuration Discovery**: Automated dual-track mDNS (`zeroconf`) and UDP broadcast discovery allowing nodes to find each other on the local network automatically.
* **Heterogeneous Hardware Pooling**: Combines x86_64 desktops, ARM64 servers, and Android phones into a single inference grid.
* **Dynamic Port Probing**: Automatically detects port collisions and probes alternative ports for HTTP API (`8080+`) and inference servers (`8081+`).
* **Triple Monitoring Interfaces**:
  1. **PySide6 Graphical Desktop App & System Tray**: Real-time status cards, worker lists, and status indicators.
  2. **Rich Terminal UI**: Live CLI status dashboard rendering active slots, throughput, and system health.
  3. **Browser Web Dashboard**: HTML/SSE web dashboard accessible from any browser at `http://localhost:8080`.
* **Process & Signal Safety**: Session-isolated process termination (`SIGTERM`/`SIGKILL`) ensures background server instances are cleanly terminated without leaving zombie processes.
* **Remote Deployment Helper**: Integrated SSH deployment script (`deploy-worker.sh`) to push and execute PyInstaller worker binaries to remote devices.

---

## 🏗 Architecture & Core Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│  Fedora / Linux Host (Root Coordinator + Optional GUI)           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ cluster.py  │──│ src/root/   │──│ src/gui/app.py          │  │
│  │  (CLI)      │  │  main.py    │  │  PySide6 Desktop GUI    │  │
│  └─────────────┘  └──────┬──────┘  └─────────────────────────┘  │
│                          │                      │               │
│                  TCP Port 52053                 ▼               │
│                  UDP Port 52052          Web Dashboard (8080)   │
└──────────────────────────┼──────────────────────────────────────┘
                           │  
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  ┌───────────┐      ┌───────────┐      ┌────────────────────────┐
  │ Linux     │      │ Windows / │      │ Android (Termux) /     │
  │ Worker    │      │ macOS     │      │ iOS Node               │
  │ (50052)   │      │ Worker    │      │ rpc-server binary      │
  └───────────┘      └───────────┘      └────────────────────────┘
```

### Network Ports Reference

| Port | Protocol | Service | Description |
|---|---|---|---|
| **`52053`** | TCP | Control Plane | Worker registration, task dispatch, heartbeat |
| **`52052`** | UDP | Discovery | UDP broadcast listener & service announcer |
| **`50052`** | TCP | llama.cpp RPC | Remote memory/tensor compute stream |
| **`8080+`** | TCP | HTTP REST API | OpenAI-compatible API & Web Dashboard |
| **`8081+`** | TCP | LLaMA Server | Fallback inference engine endpoint |

---

## 📁 File & Directory Structure

```
CLUSTER/
├── cluster.py                  # Main CLI entry point (root, worker, gui, dashboard, status, stop)
├── launcher.sh                 # Portable bash wrapper for .desktop and systemd launchers
├── ai-cluster-desktop-root.sh  # Desktop entry wrapper script
├── ai-cluster-stop.sh          # Cluster process shutdown utility
├── ai-cluster-logs.sh          # Live log tail viewer
├── ai-cluster-web.sh           # Web dashboard launch helper
├── cluster-dashboard.py        # Standalone Rich TUI dashboard
├── config.yaml                 # Configuration for ports, model paths, heartbeats, and SSH keys
├── requirements.txt            # Python dependencies (PySide6, zeroconf, psutil, rich, pyyaml)
├── Makefile                    # Target build & install shortcuts
├── setup-termux.sh             # Android Termux bootstrap installer
├── src/                        # Python application source code
│   ├── common/                 # Shared protocol, discovery, loghub, and notification components
│   ├── root/                   # Coordinator control plane and HTTP API server
│   ├── worker/                 # Worker node execution engine
│   └── gui/                    # PySide6 desktop window, system tray, and resources
├── dashboard/                  # Web dashboard HTML/JS build files
├── linux/                      # Desktop entries (.desktop) & systemd user service units
├── deploy/                     # Remote worker SSH deployment scripts
├── build/                      # PyInstaller build specification scripts
└── tests/                      # PyTest automated unit test suite
```

---

## 🚀 Installation & Setup

### Prerequisites
* Python **3.11** or higher
* `pip` and Python standard development headers

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/ficusai/CLUSTER.git
cd CLUSTER

# Install dependencies
pip install -r requirements.txt
```

### User-Space Installation (Recommended for Desktop Users)

```bash
# Installs executable to ~/.local/bin and desktop shortcut to ~/.local/share/applications
make install-local
# or
./install-local.sh
```

---

## 💻 Usage Guide (CLI & GUI)

### 1. Launching the Root Coordinator
Run the central coordinator on your primary computer:

```bash
python3 cluster.py root
```

### 2. Launching Worker Nodes
Run worker instances on auxiliary computers or devices on the same local network:

```bash
python3 cluster.py worker
```

### 3. Launching the Graphical Interface (GUI)
Start the desktop window and system tray control center:

```bash
python3 cluster.py gui
```

### 4. Interactive CLI Menu
Run without arguments for an interactive execution prompt:

```bash
python3 cluster.py
```

### 5. Stopping Cluster Services
Cleanly shut down all active root, worker, and llama.cpp processes:

```bash
python3 cluster.py stop
# or
./ai-cluster-stop.sh
```

---

## 🧪 Testing & Quality Verification

Run the automated test suite to verify network protocols, discovery mechanisms, and execution parsing:

```bash
# Execute PyTest test suite
pytest tests/

# Execute system robustness verification
python3 verify_ai_cluster_robustness.py

# Verify Python syntax across all modules
python3 -m py_compile cluster.py src/**/*.py
```

---

## 🌿 Git & Release Branching

* **Active Release Branch**: `CLUSTER-0.1v-linux-native`
* **Feature Branch**: `feature/gui-interface`
* **Remote Origin**: `https://github.com/ficusai/CLUSTER.git`

All commits within this repository maintain strict local directory boundary isolation and follow standardized release branch naming (`<PROJECT>-0.1v-linux-native`).

### Branch-Related File Changes (`feature/gui-interface`)
* `AI-Cluster.desktop`: Application desktop entry launcher with `Name=CLUSTER` and desktop actions for GUI, Root, Worker, Stop, and Logs.
* `launchers/ai-cluster.desktop`: Updated desktop launcher template for Linux environments.
* `src/gui/main_window.py`: Modular PySide6 main window with dark slate `#1a1a2e` styling, top control header bar, 7 dynamic tabs, and system tray integration.
* `src/gui/tabs/__init__.py`: Package initialization for GUI tab viewports.
* `src/gui/tabs/overview_tab.py`: Overview & Health KPI cards and live service status badges tab.
* `src/gui/tabs/topology_tab.py`: Node Topology & Worker Grid View viewport tab.
* `src/gui/tabs/model_tab.py`: GGUF Model Browser & Layer Partition Matrix tab.
* `src/gui/tabs/playground_tab.py`: Prompt Console & TTFT / t/s Telemetry viewport tab.
* `src/gui/tabs/deploy_tab.py`: SSH Remote Worker Deployment Wizard viewport tab.
* `src/gui/tabs/logs_tab.py`: Multi-Log Hub & Level Filters viewport tab.
* `src/gui/tabs/settings_tab.py`: YAML Config Manager viewport tab.

### Branch-Related File Changes (`feature/fix-signal-thread`)
* `src/root/main.py`: Guard `signal.signal()` against non-main thread crashes when running in GUI mode; falls back to `atexit.register` for cleanup.
* `src/worker/main.py`: Same guard applied to worker signal handlers to prevent crashes when launched from GUI thread.

### Branch-Related File Changes (`feat/android-connect`)
* `src/gui/tabs/deploy_tab.py`: Fully populated Android Termux deployment wizard with 7 step-by-step instructions covering package install, bootstrap, IP discovery, rpc-server setup, SSH connectivity, and Termux:Boot auto-start configuration. Includes copy-to-clipboard buttons for each command.

---

## 📄 License & Attribution

Distributed under the **MIT License**. See `LICENSE` for details.  
Maintained by the **FICUS AI Team** (`https://github.com/ficusai`).
