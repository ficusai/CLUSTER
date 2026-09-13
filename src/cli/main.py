"""main.py — Main entry point for AI Cluster CLI."""
import argparse
import sys
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__file__), ".."))

from common.loghub import LogHub
from .load_config import VERSION
from .print_banner import print_banner
from .choose_mode_interactive import choose_mode_interactive
from ._make_extra_args import _make_extra_args
from ._launch_gui import _launch_gui
from ._launch_terminal import _launch_terminal
from .check_dependencies import check_dependencies


# Decorator logs when this function is called
@LogHub.log_call("CLUSTER")
def main():
    # Create argument parser with description and custom formatting
    parser = argparse.ArgumentParser(
        description="AI Cluster Auto-Connect — Unified Launcher",
        # RawDescriptionHelpFormatter preserves formatting in epilog
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # Epilog shows usage examples after the help text
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
    
    # Define command-line arguments:
    
    # --root flag: run as root device (cluster coordinator)
    # action="store_true" means presence of flag sets value to True
    parser.add_argument("--root", action="store_true", help="Run as root device")
    
    # --worker flag: run as helper/worker node
    parser.add_argument("--worker", action="store_true", help="Run as helper/worker node")
    
    # --root-ip: specify root IP address directly (skips discovery)
    # default=None means not provided unless user specifies it
    parser.add_argument("--root-ip", default=None, help="Root IP address (skip discovery)")
    
    # --gui flag: use desktop GUI (PySide6) instead of terminal UI
    parser.add_argument("--gui", action="store_true", help="Use desktop GUI (PySide6)")
    
    # --ai-mode flag: enable AI inference cluster mode
    parser.add_argument("--ai-mode", action="store_true", help="Enable AI inference cluster mode")
    
    # --model: path to GGUF model file for AI inference
    parser.add_argument("--model", default=None, help="Path to GGUF model file")
    
    # --http-port: HTTP API port (default 8080, but can be overridden)
    # type=int ensures the value is converted to integer
    parser.add_argument("--http-port", type=int, default=None, help="HTTP API port (default: 8080)")
    
    # --ctrl-port: control port for cluster coordination (default 52053)
    parser.add_argument("--ctrl-port", type=int, default=None, help="Control port (default: 52053)")
    
    # --rpc-port: RPC port for gRPC communication (default 50052)
    parser.add_argument("--rpc-port", type=int, default=None, help="RPC port (default: 50052)")
    
    # --version flag: show version and exit
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    
    # --no-ui flag: disable progress UI, use plain text output
    parser.add_argument("--no-ui", action="store_true", help="Disable progress UI (use plain output)")

    # Parse the command-line arguments into an args object
    args = parser.parse_args()

    # If --version flag was given, print version and exit
    if args.version:
        print(f"AI Cluster Auto-Connect v{VERSION}")
        return  # Exit main function (program ends)

    # Print the banner with version info
    print_banner()
    # Check for optional dependencies and warn if missing
    check_dependencies()
    # Load configuration from config.yaml
    config = load_config()

    # Determine mode from command-line flags
    mode = None
    if args.root:
        mode = "root"
    elif args.worker:
        mode = "worker"
    # If --root-ip given without --worker, assume worker mode
    elif args.root_ip:
        mode = "worker"

    # If no mode specified via flags, ask user interactively
    if mode is None:
        mode = choose_mode_interactive()

    # Launch either GUI or terminal interface based on --gui flag
    if args.gui:
        try:
            # Try to launch GUI mode
            _launch_gui(mode, args, config=config)
        except ImportError as e:
            # PySide6 not installed - fall back to terminal
            print(f"GUI mode requires PySide6: pip install PySide6")
            print(f"Error: {e}")
            print("Falling back to terminal UI...")
            _launch_terminal(mode, args, config=config)
    else:
        # Launch terminal (non-GUI) mode
        _launch_terminal(mode, args, config=config)


def load_config(path=None):
    from .load_config import load_config as _lc
    return _lc(path)
