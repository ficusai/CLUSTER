#!/usr/bin/env python3
"""
AI Cluster Auto-Connect — Unified Launcher
Single entry point that works on any OS (Linux, macOS, Windows, Android).
Prompts user to run as root device or helper (worker) node, and auto-discovers
root devices on the network for easy selection.

Usage:
  ./cluster.py                  Interactive mode (asks root or worker)
  ./cluster.py --root           Run as root directly
  ./cluster.py --worker         Run as worker directly (auto-discovers root)
  ./cluster.py --root --gui     Run as root with desktop GUI
  ./cluster.py --worker --gui   Run as worker with desktop GUI
  ./cluster.py --worker --root-ip 192.168.1.100   Connect to specific root
"""

import argparse
import os
import secrets
import sys
import time
import socket

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from common.loghub import LogHub

VERSION = "1.3.0"

_CONFIG_LOADED = False


@LogHub.log_call("CLUSTER")
def load_config(path=None):
    global _CONFIG_LOADED
    if _CONFIG_LOADED:
        return {}
    path = path or os.path.join(os.path.dirname(__file__), "config.yaml")
    if not os.path.isfile(path):
        return {}
    try:
        import yaml
        with open(path) as f:
            cfg = yaml.safe_load(f) or {}
        _CONFIG_LOADED = True
        return cfg
    except ImportError:
        print("Note: PyYAML not installed; config.yaml ignored. Install with: pip install pyyaml")
        return {}
    except Exception as e:
        print(f"Warning: Failed to load config.yaml: {e}")
        return {}


@LogHub.log_call("CLUSTER")
def print_banner():
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║      AI Cluster Auto-Connect  v{:<6}   ║".format(VERSION))
    print("  ║   Distributed Computing Cluster Launcher     ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()


@LogHub.log_call("CLUSTER")
def choose_mode_interactive():
    print("How do you want to run this device?")
    print()
    print("  [1] Root device   (cluster coordinator)")
    print("  [2] Helper node   (worker, joins a root device)")
    print("  [3] Quit")
    print()
    while True:
        choice = input("Choice [1/2/3]: ").strip()
        if choice == "1":
            return "root"
        if choice == "2":
            return "worker"
        if choice == "3":
            print("Goodbye.")
            sys.exit(0)
        print("Invalid choice. Please enter 1, 2, or 3.")


@LogHub.log_call("CLUSTER")
def discover_roots_ui(timeout=5):
    """Discover root devices and present them to the user for selection."""
    from common.discovery import discover_roots_on_network

    print(f"\nScanning for root devices on the network (timeout: {timeout}s)...")
    print("(Make sure the root device is running cluster in root mode)")
    print()

    start = time.time()
    roots = discover_roots_on_network(timeout=timeout)
    elapsed = time.time() - start

    if not roots:
        print(f"No root devices found after {elapsed:.0f} seconds.")
        print()
        print("Options:")
        print("  [M] Enter root IP manually")
        print("  [R] Retry scan")
        print("  [Q] Quit")
        print()
        while True:
            choice = input("Choice [M/R/Q]: ").strip().upper()
            if choice == "M":
                ip = input("Enter root IP address: ").strip()
                if ip:
                    return ip, None
                print("IP address cannot be empty.")
            elif choice == "R":
                return discover_roots_ui(timeout=timeout)
            elif choice == "Q":
                print("Goodbye.")
                sys.exit(0)
            print("Invalid choice.")

    print(f"Found {len(roots)} root device(s) on the network:\n")
    print(f"  {'#':<3} {'Hostname':<20} {'IP':<18} {'Platform':<12} {'Source':<8}")
    print(f"  {'─'*3} {'─'*20} {'─'*18} {'─'*12} {'─'*8}")
    for i, r in enumerate(roots, 1):
        hostname = r.get("hostname", "unknown")[:19]
        ip = r.get("ip", "?")
        platform = r.get("platform", "unknown")[:11]
        source = r.get("source", "mDNS")[:7]
        print(f"  {i:<3} {hostname:<20} {ip:<18} {platform:<12} {source:<8}")
    print()

    while True:
        choice = input(f"Select root device [1-{len(roots)}] or [M]anual / [R]etry / [Q]uit: ").strip().upper()
        if choice == "M":
            ip = input("Enter root IP address: ").strip()
            if ip:
                return ip, None
        elif choice == "R":
            return discover_roots_ui(timeout=timeout)
        elif choice == "Q":
            print("Goodbye.")
            sys.exit(0)
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(roots):
                    r = roots[idx]
                    return r["ip"], r
            except ValueError:
                pass
        print(f"Invalid choice. Enter 1-{len(roots)}, M, R, or Q.")


@LogHub.log_call("CLUSTER")
def _make_extra_args(args, extra=None, config=None):
    extra = extra or {}
    config = config or {}
    out = {}

    if args.ai_mode or config.get("ai", {}).get("model"):
        out["ai_mode"] = True
    if args.model:
        out["model_path"] = args.model
    elif config.get("ai", {}).get("model"):
        out["model_path"] = os.path.join(os.path.dirname(__file__), config["ai"]["model"])

    if args.http_port is not None:
        out["http_port"] = args.http_port
    elif config.get("root", {}).get("http_port"):
        out["http_port"] = config["root"]["http_port"]

    if args.ctrl_port is not None:
        out["ctrl_port"] = args.ctrl_port
    elif config.get("network", {}).get("ctrl_port"):
        out["ctrl_port"] = config["network"]["ctrl_port"]

    if args.rpc_port is not None:
        out["rpc_port"] = args.rpc_port
    elif config.get("network", {}).get("rpc_port"):
        out["rpc_port"] = config["network"]["rpc_port"]

    if config.get("security", {}).get("api_token"):
        out["api_token"] = config["security"]["api_token"]
    elif not os.environ.get("AI_CLUSTER_API_TOKEN") and not getattr(args, "api_token", None):
        out["api_token"] = secrets.token_urlsafe(32)

    out.update(extra)
    return out


@LogHub.log_call("CLUSTER")
def run_as_root(args, ui=None, config=None):
    from root.main import main as root_main
    saved_argv = sys.argv
    sys.argv = [saved_argv[0]]
    try:
        root_main(ui=ui, **_make_extra_args(args, config=config))
    finally:
        sys.argv = saved_argv


@LogHub.log_call("CLUSTER")
def run_as_worker(root_ip, args, ui=None, config=None):
    from worker.main import main as worker_main
    extra = {}
    if root_ip:
        extra["root_ip"] = root_ip
    saved_argv = sys.argv
    sys.argv = [saved_argv[0]]
    try:
        worker_main(ui=ui, **_make_extra_args(args, extra, config))
    finally:
        sys.argv = saved_argv


@LogHub.log_call("CLUSTER")
def _launch_gui(mode, args, config=None):
    from gui.app import run_gui
    kwargs = _make_extra_args(args, config=config) if mode == "root" else {}

    @LogHub.log_call("CLUSTER")
    def cluster_fn(**kw):
        if mode == "root":
            run_as_root(args, config=config)
        else:
            root_ip = args.root_ip
            if not root_ip:
                import socket as _socket
                import threading
                from common.discovery import discover_roots_on_network, UDPBroadcastDiscovery
                from common.protocol import parse_msg

                root_found = [None]
                @LogHub.log_call("CLUSTER")
                def wait_for_root():
                    roots = discover_roots_on_network(timeout=5)
                    if roots:
                        root_found[0] = roots[0]["ip"]
                        return
                    udp = UDPBroadcastDiscovery()
                    @LogHub.log_call("CLUSTER")
                    def on_udp(data, addr):
                        try:
                            msg = parse_msg(data)
                            if msg.get("type") == "root_announce":
                                root_found[0] = addr[0]
                        except Exception:
                            pass
                    udp.start_listener(on_udp)
                    for _ in range(3):
                        from common.protocol import make_msg
                        udp.broadcast(make_msg("worker_discover"))
                        time.sleep(2)
                    udp.stop()

                t = threading.Thread(target=wait_for_root, daemon=True)
                t.start()
                t.join(timeout=8)

                if root_found[0]:
                    root_ip = root_found[0]
                else:
                    print("No root found. Exiting.")
                    return

            run_as_worker(root_ip, args, config=config)

    run_gui(
        mode=mode,
        cluster_fn=cluster_fn,
        version=VERSION,
    )


@LogHub.log_call("CLUSTER")
def _launch_terminal(mode, args, config=None):
    if mode == "root":
        print("Starting as ROOT device (cluster coordinator)...\n")
        from common.progress_ui import send_notification, ProgressUI
        send_notification("AI Cluster Auto-Connect", "Starting as ROOT device...")
        ui = None
        if not args.no_ui:
            ui = ProgressUI(mode="root")
            ui.set_system_info(version=VERSION)
            ui.start()
        run_as_root(args, ui=ui, config=config)

    elif mode == "worker":
        root_ip = args.root_ip
        selected_root = None

        if not root_ip:
            root_ip, selected_root = discover_roots_ui()

        if root_ip:
            print(f"\nConnecting to root device at {root_ip}...\n")
            from common.progress_ui import send_notification, ProgressUI
            send_notification("AI Cluster Auto-Connect", f"Connecting to root at {root_ip}...")
            ui = None
            if not args.no_ui:
                ui = ProgressUI(mode="worker")
                ui.set_system_info(version=VERSION)
                ui.start()
            run_as_worker(root_ip, args, ui=ui, config=config)
        else:
            print("No root device selected. Exiting.")
            sys.exit(1)


@LogHub.log_call("CLUSTER")
def check_dependencies():
    """Check for optional dependencies and warn if missing."""
    missing = []
    try:
        import zeroconf
    except ImportError:
        missing.append("zeroconf (for mDNS discovery)")
    try:
        import psutil
    except ImportError:
        missing.append("psutil (for CPU/RAM detection)")

    if missing:
        print("Note: Some optional dependencies are missing:")
        for m in missing:
            print(f"  - {m}")
        print("  Core functionality (UDP broadcast) will still work.")
        print("  Install with: pip install zeroconf psutil")
        print()


@LogHub.log_call("CLUSTER")
def main():
    parser = argparse.ArgumentParser(
        description="AI Cluster Auto-Connect — Unified Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s                    Interactive mode (choose root or worker)
  %(prog)s --root             Run as root device (coordinator)
  %(prog)s --root --ai-mode   Run as root with AI inference cluster
  %(prog)s --worker           Run as helper/worker (auto-discover root)
  %(prog)s --root --gui       Run as root with desktop GUI
  %(prog)s --worker --gui     Run as worker with desktop GUI
  %(prog)s --worker --root-ip 192.168.1.100  Connect to specific root
        """,
    )
    parser.add_argument("--root", action="store_true", help="Run as root device")
    parser.add_argument("--worker", action="store_true", help="Run as helper/worker node")
    parser.add_argument("--root-ip", default=None, help="Root IP address (skip discovery)")
    parser.add_argument("--gui", action="store_true", help="Use desktop GUI (PySide6)")
    parser.add_argument("--ai-mode", action="store_true", help="Enable AI inference cluster mode")
    parser.add_argument("--model", default=None, help="Path to GGUF model file")
    parser.add_argument("--http-port", type=int, default=None, help="HTTP API port (default: 8080)")
    parser.add_argument("--ctrl-port", type=int, default=None, help="Control port (default: 52053)")
    parser.add_argument("--rpc-port", type=int, default=None, help="RPC port (default: 50052)")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument("--no-ui", action="store_true", help="Disable progress UI (use plain output)")

    args = parser.parse_args()

    if args.version:
        print(f"AI Cluster Auto-Connect v{VERSION}")
        return

    print_banner()
    check_dependencies()
    config = load_config()

    mode = None
    if args.root:
        mode = "root"
    elif args.worker:
        mode = "worker"
    elif args.root_ip:
        mode = "worker"

    if mode is None:
        mode = choose_mode_interactive()

    if args.gui:
        try:
            _launch_gui(mode, args, config=config)
        except ImportError as e:
            print(f"GUI mode requires PySide6: pip install PySide6")
            print(f"Error: {e}")
            print("Falling back to terminal UI...")
            _launch_terminal(mode, args, config=config)
    else:
        _launch_terminal(mode, args, config=config)


if __name__ == "__main__":
    main()