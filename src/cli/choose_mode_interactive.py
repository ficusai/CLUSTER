"""choose_mode_interactive.py — Interactive mode selection prompt."""
import sys
from common.loghub import LogHub


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
