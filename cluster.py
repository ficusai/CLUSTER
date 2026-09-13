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
import os
import sys

# Add the "src" folder (inside this project) to Python's search path
# This lets us import modules from src/ like "from common.loghub import LogHub"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from cli.main import main

if __name__ == "__main__":
    main()
