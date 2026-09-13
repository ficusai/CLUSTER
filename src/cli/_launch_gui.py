"""_launch_gui.py — Launch GUI mode (PySide6)."""
import sys
import time
import socket
import threading
from common.loghub import LogHub
from common.discovery import discover_roots_on_network, UDPBroadcastDiscovery
from common.protocol import parse_msg, make_msg
from .load_config import VERSION
from ._make_extra_args import _make_extra_args
from .run_as_root import run_as_root
from .run_as_worker import run_as_worker


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
