"""api_handler.py — APIHandler class (nested inside start_http_api mixin)."""
import json
import os
import threading
import time
from http.server import SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from common.loghub import LogHub
from ..utils import build_status_dict as _build_status_dict_imported
