"""discover_roots_ui.py — Interactive root device discovery and selection."""
import sys
import time
from common.loghub import LogHub
from common.discovery import discover_roots_on_network


# Decorator logs when this function is called
@LogHub.log_call("CLUSTER")
def discover_roots_ui(timeout=5):
    """Discover root devices and present them to the user for selection."""
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
