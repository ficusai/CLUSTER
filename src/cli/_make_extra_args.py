"""_make_extra_args.py — Merge CLI args, config, and extras into kwargs."""
import os
import secrets
from common.loghub import LogHub


# Decorator logs when this function is called
@LogHub.log_call("CLUSTER")
def _make_extra_args(args, extra=None, config=None):
    # extra and config default to None, convert to empty dicts if so
    # This avoids "NoneType" errors when trying to call .get() on them
    extra = extra or {}
    config = config or {}
    # Create output dictionary that will hold all combined arguments
    out = {}

    # Check if AI mode is enabled via command line OR config file
    # args.ai_mode comes from --ai-mode flag
    # config.get("ai", {}).get("model") checks config.yaml for ai.model setting
    if args.ai_mode or config.get("ai", {}).get("model"):
        out["ai_mode"] = True  # Enable AI inference cluster mode

    # Handle model path - command line argument takes priority over config
    if args.model:
        # User provided --model path on command line
        out["model_path"] = args.model
    elif config.get("ai", {}).get("model"):
        # No command line model, but config.yaml has ai.model
        # Join the script's directory with the relative path from config
        out["model_path"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", config["ai"]["model"])

    # Handle HTTP port - command line overrides config
    if args.http_port is not None:
        out["http_port"] = args.http_port
    elif config.get("root", {}).get("http_port"):
        out["http_port"] = config["root"]["http_port"]

    # Handle control port - command line overrides config
    if args.ctrl_port is not None:
        out["ctrl_port"] = args.ctrl_port
    elif config.get("network", {}).get("ctrl_port"):
        out["ctrl_port"] = config["network"]["ctrl_port"]

    # Handle RPC port - command line overrides config
    if args.rpc_port is not None:
        out["rpc_port"] = args.rpc_port
    elif config.get("network", {}).get("rpc_port"):
        out["rpc_port"] = config["network"]["rpc_port"]

    # Handle API token for authentication
    # Priority: config file > environment variable > generate new random token
    if config.get("security", {}).get("api_token"):
        out["api_token"] = config["security"]["api_token"]
    elif not os.environ.get("AI_CLUSTER_API_TOKEN") and not getattr(args, "api_token", None):
        # Generate a secure random URL-safe token (32 bytes = 43 chars)
        out["api_token"] = secrets.token_urlsafe(32)

    # Merge any additional extra arguments passed in
    out.update(extra)
    return out
