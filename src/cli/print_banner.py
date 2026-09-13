"""print_banner.py — Print the AI Cluster banner."""
from common.loghub import LogHub
from .load_config import VERSION


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
