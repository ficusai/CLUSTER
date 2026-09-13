"""run_as_root.py — Run as root device (cluster coordinator)."""
import sys
from common.loghub import LogHub
from ._make_extra_args import _make_extra_args


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
