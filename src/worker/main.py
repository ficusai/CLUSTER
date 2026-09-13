"""main.py — ClusterWorker entry point (thin wrapper around modular packages)."""
import argparse
import signal
import sys
import threading

sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__file__), ".."))

from common.protocol import CTRL_PORT_DEFAULT, RPC_PORT_DEFAULT
from .worker.cluster_worker import ClusterWorker


def main(ui=None, **kwargs):
    parser = argparse.ArgumentParser(description="cluster-worker — auto-connect worker node")
    parser.add_argument("--port", type=int, default=CTRL_PORT_DEFAULT,
                        help=f"Control port (default: {CTRL_PORT_DEFAULT})")
    parser.add_argument("--rpc-port", type=int, default=RPC_PORT_DEFAULT,
                        help=f"RPC port for llama.cpp (default: {RPC_PORT_DEFAULT})")
    parser.add_argument("--root-ip", default=None,
                        help="Root IP (skip discovery)")
    parser.add_argument("--ai-mode", action="store_true",
                        help="Auto-start rpc-server for AI cluster")
    args = parser.parse_args()

    worker = ClusterWorker(
        ctrl_port=kwargs.get("ctrl_port", args.port),
        rpc_port=kwargs.get("rpc_port", args.rpc_port),
        root_ip=kwargs.get("root_ip", args.root_ip),
        ai_mode=kwargs.get("ai_mode", args.ai_mode),
        ui=ui,
    )

    def handle_sig(sig, frame):
        from common.loghub import LogHub
        LogHub().info("WORKER", "Shutting down...")
        worker.stop()
        sys.exit(0)

    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, handle_sig)
        signal.signal(signal.SIGTERM, handle_sig)
    else:
        import atexit
        atexit.register(handle_sig, signal.SIGTERM, None)

    worker.run()


if __name__ == "__main__":
    main()
