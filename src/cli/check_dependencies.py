"""check_dependencies.py — Check for optional dependencies and warn if missing."""
from common.loghub import LogHub


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
