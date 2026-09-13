"""run_as_worker.py — Run as worker node (helper/worker)."""
import sys
from common.loghub import LogHub
from ._make_extra_args import _make_extra_args


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
