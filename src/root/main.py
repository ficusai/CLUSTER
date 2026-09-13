"""main.py — ClusterRoot entry point (thin wrapper around modular packages)."""
import argparse
import signal
import sys
import threading
import time

sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__file__), ".."))

from common.protocol import CTRL_PORT_DEFAULT, RPC_PORT_DEFAULT
from .cluster.cluster_root import ClusterRoot


def main(ui=None, **kwargs):
    parser = argparse.ArgumentParser(description="cluster-root — main coordinator")
    parser.add_argument("--port", type=int, default=CTRL_PORT_DEFAULT,
                        help=f"Control port (default: {CTRL_PORT_DEFAULT})")
    parser.add_argument("--rpc-port", type=int, default=RPC_PORT_DEFAULT,
                        help=f"Local RPC port (default: {RPC_PORT_DEFAULT})")
    parser.add_argument("--ai-mode", action="store_true",
                        help="Enable AI inference cluster mode")
    parser.add_argument("--model", default=None,
                        help="Path to GGUF model file")
    parser.add_argument("--http-port", type=int, default=8080,
                        help="HTTP API port (default: 8080)")
    parser.add_argument("--api-token", default=None,
                        help="Bearer token for /api/task/exec (env: AI_CLUSTER_API_TOKEN)")
    args = parser.parse_args()

    ctrl_port = kwargs.get("ctrl_port", args.port)
    rpc_port = kwargs.get("rpc_port", args.rpc_port)
    ai_mode = kwargs.get("ai_mode", args.ai_mode)
    model_path = kwargs.get("model_path", args.model)
    http_port = kwargs.get("http_port", args.http_port) or 8080
    api_token = kwargs.get("api_token", args.api_token)

    root = ClusterRoot(
        ctrl_port=ctrl_port,
        rpc_port=rpc_port,
        ai_mode=ai_mode,
        model_path=model_path,
        http_port=http_port,
        ui=ui,
        api_token=api_token,
    )

    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, lambda s, f: root.stop())
        signal.signal(signal.SIGTERM, lambda s, f: root.stop())
    else:
        import atexit
        atexit.register(root.stop)

    root.run()


if __name__ == "__main__":
    main()
