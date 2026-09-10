import os
import socket
import tempfile
import threading
import time

import pytest

from unittest.mock import MagicMock, patch

from common.protocol import CTRL_PORT_DEFAULT
from root.main import ClusterRoot


def _hold_port(port, stop_event):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(1)
    while not stop_event.is_set():
        try:
            srv.settimeout(0.1)
            conn, _ = srv.accept()
            conn.close()
        except Exception:
            pass
    srv.close()


def test_root_llama_port_fallback():
    # Hold 8081 so root must fall back to 8082
    stop = threading.Event()
    t = threading.Thread(target=_hold_port, args=(8081, stop), daemon=True)
    t.start()
    time.sleep(0.1)

    mock_proc = MagicMock()
    mock_proc.pid = 999999
    mock_proc.poll.return_value = None

    fake_model = os.path.join(tempfile.gettempdir(), "fake_model.gguf")

    root = ClusterRoot(ctrl_port=CTRL_PORT_DEFAULT + 9999, ai_mode=False)
    root.model_path = fake_model
    try:
        with patch("subprocess.Popen", return_value=mock_proc), patch("root.main.time.sleep", return_value=None):
            root.start_llama_server()
            # Should have fallen back away from 8081
            assert root.llama_http_port != 8081
            assert root.llama_process is not None
            assert root.llama_process.poll() is None
    finally:
        root.stop()
        stop.set()
        t.join(timeout=1)
