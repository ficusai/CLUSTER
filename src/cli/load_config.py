#!/usr/bin/env python3
"""load_config.py — Load configuration from config.yaml."""
# Import standard Python libraries that provide common functionality
import os        # For file and directory operations, environment variables
import sys       # For system-level operations like exiting the program, modifying argv

# Add the "src" folder (inside this project) to Python's search path
# This lets us import modules from src/ like "from common.loghub import LogHub"
# os.path.dirname(__file__) gets the folder where this cluster.py file lives
# os.path.join combines that folder path with "src" to make a full path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "config.yaml")
    
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
