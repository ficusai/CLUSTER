#!/usr/bin/env python3
# This line tells the operating system to use Python 3 to run this script.
# It's called a "shebang" and makes the file executable directly (like ./cluster.py)
# instead of needing to type "python3 cluster.py" every time.
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

# Import standard Python libraries that provide common functionality
import argparse  # For parsing command-line arguments (like --root, --worker, --gui)
import os        # For file and directory operations, environment variables
import secrets   # For generating secure random tokens (used for API authentication)
import sys       # For system-level operations like exiting the program, modifying argv
import time      # For timing operations (measuring how long network scans take)
import socket    # For network operations (IP addresses, hostnames, connections)

# Add the "src" folder (inside this project) to Python's search path
# This lets us import modules from src/ like "from common.loghub import LogHub"
# os.path.dirname(__file__) gets the folder where this cluster.py file lives
# os.path.join combines that folder path with "src" to make a full path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import LogHub from our common logging module
# LogHub provides the @LogHub.log_call decorator that logs when functions are called
from common.loghub import LogHub

# Version string for this cluster launcher
# Used in banners, GUI titles, and version reporting
VERSION = "1.3.0"

# Global flag to track whether config.yaml has been loaded
# Prevents loading the config file multiple times (which would be wasteful)
# Starts as False, becomes True after first successful load
_CONFIG_LOADED = False


# This decorator (@LogHub.log_call) logs every time this function is called
# The "CLUSTER" argument is a label used in the log output
# The function loads configuration from config.yaml file
@LogHub.log_call("CLUSTER")
def load_config(path=None):
    # Access the global _CONFIG_LOADED flag so we can modify it
    global _CONFIG_LOADED
    
    # If config was already loaded, return empty dict to avoid re-loading
    # This saves time and prevents overwriting settings from earlier loads
    if _CONFIG_LOADED:
        return {}
    
    # If no path provided, default to config.yaml in the same folder as this script
    # os.path.dirname(__file__) = folder containing cluster.py
    # os.path.join combines it with "config.yaml" to make full path
    path = path or os.path.join(os.path.dirname(__file__), "config.yaml")
    
    # Check if the config file actually exists at that path
    # os.path.isfile returns True only for regular files (not folders)
    if not os.path.isfile(path):
        return {}  # Return empty config if file doesn't exist
    
    # Try to load and parse the YAML config file
    try:
        import yaml  # PyYAML library for reading YAML files
        with open(path) as f:  # Open the file for reading
            # yaml.safe_load parses YAML safely (no arbitrary code execution)
            # Returns a Python dict, or None if file is empty
            # "or {}" converts None to empty dict
            cfg = yaml.safe_load(f) or {}
        _CONFIG_LOADED = True  # Mark config as loaded so we don't load again
        return cfg  # Return the parsed configuration dictionary
    
    # Handle case where PyYAML is not installed
    except ImportError:
        print("Note: PyYAML not installed; config.yaml ignored. Install with: pip install pyyaml")
        return {}  # Return empty config, program continues without config file
    
    # Handle any other errors (malformed YAML, permission issues, etc.)
    except Exception as e:
        print(f"Warning: Failed to load config.yaml: {e}")
        return {}  # Return empty config, program continues with defaults


# Decorator logs when this function is called
@LogHub.log_call("CLUSTER")
def print_banner():
    # Print a blank line for visual spacing
    print()
    # Print the top border of the banner box
    print("  ╔══════════════════════════════════════════════╗")
    # Print the title line with version number
    # {:<6} formats VERSION left-aligned in a 6-character wide field
    print("  ║      AI Cluster Auto-Connect  v{:<6}   ║".format(VERSION))
    # Print the subtitle line
    print("  ║   Distributed Computing Cluster Launcher     ║")
    # Print the bottom border of the banner box
    print("  ╚══════════════════════════════════════════════╝")
    # Print a blank line after the banner
    print()


# Decorator logs when this function is called
@LogHub.log_call("CLUSTER")
def choose_mode_interactive():
    # Print the question asking user what role this device should play
    print("How do you want to run this device?")
    print()
    # Print option 1: Root device (the coordinator/manager of the cluster)
    print("  [1] Root device   (cluster coordinator)")
    # Print option 2: Helper node (worker that joins a root device)
    print("  [2] Helper node   (worker, joins a root device)")
    # Print option 3: Quit the program
    print("  [3] Quit")
    print()
    
    # Loop forever until user makes a valid choice
    while True:
        # Get user input, strip whitespace, and store in choice variable
        choice = input("Choice [1/2/3]: ").strip()
        # If user enters 1, return "root" to indicate root mode
        if choice == "1":
            return "root"
        # If user enters 2, return "worker" to indicate worker mode
        if choice == "2":
            return "worker"
        # If user enters 3, print goodbye and exit the program completely
        if choice == "3":
            print("Goodbye.")
            sys.exit(0)  # Exit with code 0 (success)
        # If input was anything else, show error and loop again
        print("Invalid choice. Please enter 1, 2, or 3.")


# Decorator logs when this function is called
@LogHub.log_call("CLUSTER")
def discover_roots_ui(timeout=5):
    """Discover root devices and present them to the user for selection."""
    # Import the network discovery function from our common module
    # This function scans the network for devices advertising as cluster roots
    from common.discovery import discover_roots_on_network

    # Tell user we're scanning, show the timeout value
    print(f"\nScanning for root devices on the network (timeout: {timeout}s)...")
    # Remind user that root device must be running in root mode
    print("(Make sure the root device is running cluster in root mode)")
    print()
    
    # Record the start time (in seconds since epoch) to measure scan duration
    start = time.time()
    # Call the discovery function, which returns a list of found root devices
    # Each root is a dict with keys like: ip, hostname, platform, source
    roots = discover_roots_on_network(timeout=timeout)
    # Calculate how many seconds the scan took
    elapsed = time.time() - start

    # If no roots were found, show options to the user
    if not roots:
        print(f"No root devices found after {elapsed:.0f} seconds.")
        print()
        print("Options:")
        print("  [M] Enter root IP manually")
        print("  [R] Retry scan")
        print("  [Q] Quit")
        print()
        
        # Loop until user makes a valid choice
        while True:
            choice = input("Choice [M/R/Q]: ").strip().upper()
            # Manual IP entry
            if choice == "M":
                ip = input("Enter root IP address: ").strip()
                if ip:
                    # Return the IP and None (no root info dict since manual)
                    return ip, None
                print("IP address cannot be empty.")
            # Retry the scan by calling this function recursively
            elif choice == "R":
                return discover_roots_ui(timeout=timeout)
            # Quit the program
            elif choice == "Q":
                print("Goodbye.")
                sys.exit(0)
            # Invalid input
            print("Invalid choice.")

    # Roots were found - display them in a formatted table
    print(f"Found {len(roots)} root device(s) on the network:\n")
    # Print table header with column names
    print(f"  {'#':<3} {'Hostname':<20} {'IP':<18} {'Platform':<12} {'Source':<8}")
    # Print separator line
    print(f"  {'─'*3} {'─'*20} {'─'*18} {'─'*12} {'─'*8}")
    # Loop through each found root and print its info
    for i, r in enumerate(roots, 1):  # enumerate starts counting at 1
        # Get hostname, truncate to 19 chars if longer
        hostname = r.get("hostname", "unknown")[:19]
        # Get IP address, default to "?" if missing
        ip = r.get("ip", "?")
        # Get platform, truncate to 11 chars
        platform = r.get("platform", "unknown")[:11]
        # Get discovery source (mDNS, UDP broadcast, etc.), truncate to 7 chars
        source = r.get("source", "mDNS")[:7]
        # Print formatted row with index and root details
        print(f"  {i:<3} {hostname:<20} {ip:<18} {platform:<12} {source:<8}")
    print()

    # Loop until user selects a valid root or chooses manual/retry/quit
    while True:
        # Prompt shows valid range based on number of found roots
        choice = input(f"Select root device [1-{len(roots)}] or [M]anual / [R]etry / [Q]uit: ").strip().upper()
        # Manual IP entry
        if choice == "M":
            ip = input("Enter root IP address: ").strip()
            if ip:
                return ip, None
        # Retry scan
        elif choice == "R":
            return discover_roots_ui(timeout=timeout)
        # Quit
        elif choice == "Q":
            print("Goodbye.")
            sys.exit(0)
        # Try to parse as a number (1-based index)
        else:
            try:
                idx = int(choice) - 1  # Convert to 0-based index
                # Check if index is in valid range
                if 0 <= idx < len(roots):
                    r = roots[idx]  # Get the selected root dict
                    return r["ip"], r  # Return IP and full root info
            except ValueError:
                # Input wasn't a number, ignore and show error
                pass
        # If we reach here, input was invalid
        print(f"Invalid choice. Enter 1-{len(roots)}, M, R, or Q.")


# Decorator logs when this function is called
@LogHub.log_call("CLUSTER")
def _make_extra_args(args, extra=None, config=None):
    # extra and config default to None, convert to empty dicts if so
    # This avoids "NoneType" errors when trying to call .get() on them
    extra = extra or {}
    config = config or {}
    # Create output dictionary that will hold all combined arguments
    out = {}

    # Check if AI mode is enabled via command line OR config file
    # args.ai_mode comes from --ai-mode flag
    # config.get("ai", {}).get("model") checks config.yaml for ai.model setting
    if args.ai_mode or config.get("ai", {}).get("model"):
        out["ai_mode"] = True  # Enable AI inference cluster mode

    # Handle model path - command line argument takes priority over config
    if args.model:
        # User provided --model path on command line
        out["model_path"] = args.model
    elif config.get("ai", {}).get("model"):
        # No command line model, but config.yaml has ai.model
        # Join the script's directory with the relative path from config
        out["model_path"] = os.path.join(os.path.dirname(__file__), config["ai"]["model"])

    # Handle HTTP port - command line overrides config
    if args.http_port is not None:
        out["http_port"] = args.http_port
    elif config.get("root", {}).get("http_port"):
        out["http_port"] = config["root"]["http_port"]

    # Handle control port - command line overrides config
    if args.ctrl_port is not None:
        out["ctrl_port"] = args.ctrl_port
    elif config.get("network", {}).get("ctrl_port"):
        out["ctrl_port"] = config["network"]["ctrl_port"]

    # Handle RPC port - command line overrides config
    if args.rpc_port is not None:
        out["rpc_port"] = args.rpc_port
    elif config.get("network", {}).get("rpc_port"):
        out["rpc_port"] = config["network"]["rpc_port"]

    # Handle API token for authentication
    # Priority: config file > environment variable > generate new random token
    if config.get("security", {}).get("api_token"):
        out["api_token"] = config["security"]["api_token"]
    elif not os.environ.get("AI_CLUSTER_API_TOKEN") and not getattr(args, "api_token", None):
        # Generate a secure random URL-safe token (32 bytes = 43 chars)
        out["api_token"] = secrets.token_urlsafe(32)

    # Merge any additional extra arguments passed in
    out.update(extra)
    return out


# Decorator logs when this function is called
@LogHub.log_call("CLUSTER")
def run_as_root(args, ui=None, config=None):
    # Import the root node's main function
    from root.main import main as root_main
    
    # Save the original command-line arguments (sys.argv)
    # We temporarily replace sys.argv because root.main might parse its own args
    saved_argv = sys.argv
    # Replace sys.argv with just the script name (no extra args)
    sys.argv = [saved_argv[0]]
    try:
        # Call the root main function with UI and combined arguments
        # _make_extra_args merges command line, config, and defaults
        root_main(ui=ui, **_make_extra_args(args, config=config))
    finally:
        # Always restore original sys.argv, even if an error occurred
        sys.argv = saved_argv


# Decorator logs when this function is called
@LogHub.log_call("CLUSTER")
def run_as_worker(root_ip, args, ui=None, config=None):
    # Import the worker node's main function
    from worker.main import main as worker_main
    
    # Prepare extra arguments specific to worker mode
    extra = {}
    if root_ip:
        # Add the root IP address so worker knows where to connect
        extra["root_ip"] = root_ip
    
    # Save original sys.argv and temporarily replace it (same pattern as root)
    saved_argv = sys.argv
    sys.argv = [saved_argv[0]]
    try:
        # Call worker main with UI, root IP, and combined arguments
        worker_main(ui=ui, **_make_extra_args(args, extra, config))
    finally:
        # Restore original sys.argv
        sys.argv = saved_argv


# Decorator logs when this function is called
@LogHub.log_call("CLUSTER")
def _launch_gui(mode, args, config=None):
    # Import the GUI runner function from our gui module
    from gui.app import run_gui
    
    # For root mode, prepare combined arguments; for worker, use empty dict
    # Worker gets root IP via discovery inside cluster_fn below
    kwargs = _make_extra_args(args, config=config) if mode == "root" else {}

    # Define a nested function that the GUI will call when user clicks "Start"
    # This function encapsulates the logic for starting root or worker
    @LogHub.log_call("CLUSTER")
    def cluster_fn(**kw):
        if mode == "root":
            # Root mode: just call run_as_root with args and config
            run_as_root(args, config=config)
        else:
            # Worker mode: need to find root IP first
            root_ip = args.root_ip  # Check if user provided --root-ip
            if not root_ip:
                # No root IP given - need to discover automatically
                import socket as _socket
                import threading
                from common.discovery import discover_roots_on_network, UDPBroadcastDiscovery
                from common.protocol import parse_msg

                # List to hold found root IP (using list so nested function can modify it)
                root_found = [None]
                
                # Define the function that will run in a background thread
                @LogHub.log_call("CLUSTER")
                def wait_for_root():
                    # First try mDNS discovery (5 second timeout)
                    roots = discover_roots_on_network(timeout=5)
                    if roots:
                        root_found[0] = roots[0]["ip"]
                        return
                    
                    # If mDNS failed, try UDP broadcast discovery
                    udp = UDPBroadcastDiscovery()
                    
                    # Callback function for when UDP packets arrive
                    @LogHub.log_call("CLUSTER")
                    def on_udp(data, addr):
                        try:
                            msg = parse_msg(data)  # Parse the received message
                            # Check if it's a root announcement message
                            if msg.get("type") == "root_announce":
                                root_found[0] = addr[0]  # Store sender's IP
                        except Exception:
                            pass  # Ignore parse errors
                    
                    udp.start_listener(on_udp)  # Start listening for broadcasts
                    
                    # Send 3 discovery broadcasts, 2 seconds apart
                    for _ in range(3):
                        from common.protocol import make_msg
                        udp.broadcast(make_msg("worker_discover"))  # Send "I'm a worker looking for root"
                        time.sleep(2)
                    udp.stop()  # Stop the listener

                # Create and start the discovery thread (daemon=True means it won't block exit)
                t = threading.Thread(target=wait_for_root, daemon=True)
                t.start()
                # Wait up to 8 seconds for the thread to finish
                t.join(timeout=8)

                # Check if we found a root
                if root_found[0]:
                    root_ip = root_found[0]
                else:
                    print("No root found. Exiting.")
                    return  # Exit the cluster_fn, don't start worker

            # Now we have a root_ip, start the worker
            run_as_worker(root_ip, args, config=config)

    # Launch the GUI with the cluster_fn as the start callback
    run_gui(
        mode=mode,           # "root" or "worker"
        cluster_fn=cluster_fn,  # Function to call when user clicks Start
        version=VERSION,     # Pass version for display in GUI
    )


# Decorator logs when this function is called
@LogHub.log_call("CLUSTER")
def _launch_terminal(mode, args, config=None):
    if mode == "root":
        # Print status message to terminal
        print("Starting as ROOT device (cluster coordinator)...\n")
        # Import notification and progress UI classes
        from common.progress_ui import send_notification, ProgressUI
        # Send desktop notification (if supported)
        send_notification("AI Cluster Auto-Connect", "Starting as ROOT device...")
        
        ui = None  # Default to no UI
        # If --no-ui flag was NOT provided, create and start progress UI
        if not args.no_ui:
            ui = ProgressUI(mode="root")  # Create progress UI for root mode
            ui.set_system_info(version=VERSION)  # Set version info for display
            ui.start()  # Start the UI (shows progress, stats, etc.)
        
        # Run the root node with the UI (or None)
        run_as_root(args, ui=ui, config=config)

    elif mode == "worker":
        # Get root IP from command line (--root-ip)
        root_ip = args.root_ip
        selected_root = None  # Will hold full root info if discovered

        # If no root IP provided, run interactive discovery
        if not root_ip:
            root_ip, selected_root = discover_roots_ui()

        # If we have a root IP (from args or discovery), connect to it
        if root_ip:
            print(f"\nConnecting to root device at {root_ip}...\n")
            from common.progress_ui import send_notification, ProgressUI
            send_notification("AI Cluster Auto-Connect", f"Connecting to root at {root_ip}...")
            
            ui = None
            if not args.no_ui:
                ui = ProgressUI(mode="worker")  # Create progress UI for worker mode
                ui.set_system_info(version=VERSION)
                ui.start()
            
            # Run the worker node
            run_as_worker(root_ip, args, ui=ui, config=config)
        else:
            # No root IP and user quit discovery
            print("No root device selected. Exiting.")
            sys.exit(1)  # Exit with error code 1


# Decorator logs when this function is called
@LogHub.log_call("CLUSTER")
def check_dependencies():
    """Check for optional dependencies and warn if missing."""
    # List to collect names of missing optional packages
    missing = []
    
    # Try to import zeroconf (for mDNS/Bonjour network discovery)
    try:
        import zeroconf
    except ImportError:
        missing.append("zeroconf (for mDNS discovery)")
    
    # Try to import psutil (for CPU/RAM/disk usage monitoring)
    try:
        import psutil
    except ImportError:
        missing.append("psutil (for CPU/RAM detection)")

    # If any optional dependencies are missing, warn the user
    if missing:
        print("Note: Some optional dependencies are missing:")
        for m in missing:
            print(f"  - {m}")
        print("  Core functionality (UDP broadcast) will still work.")
        print("  Install with: pip install zeroconf psutil")
        print()


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


# This block only runs when the script is executed directly (not imported)
# __name__ is "__main__" when run as: python3 cluster.py
# __name__ is "cluster" when imported as: import cluster
if __name__ == "__main__":
    main()  # Call the main function to start the program