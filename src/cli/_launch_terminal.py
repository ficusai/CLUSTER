"""_launch_terminal.py — Launch terminal (non-GUI) mode."""
import sys
from common.loghub import LogHub
from common.progress_ui import send_notification, ProgressUI
from .load_config import VERSION
from .discover_roots_ui import discover_roots_ui
from .run_as_root import run_as_root
from .run_as_worker import run_as_worker


# Decorator logs when this function is called
@LogHub.log_call("CLUSTER")
def _launch_terminal(mode, args, config=None):
    if mode == "root":
        # Print status message to terminal
        print("Starting as ROOT device (cluster coordinator)...\n")
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
