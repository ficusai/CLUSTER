import json
import socket
import threading
import time

import pytest

from common.protocol import (
    CTRL_PORT_DEFAULT,
    MSG_REGISTER,
    MSG_REGISTER_ACK,
    MSG_TASK,
    MSG_TASK_RESULT,
    MSG_PING,
    MSG_PONG,
    MSG_DISCONNECT,
    ControlProtocol,
    make_msg,
    parse_msg,
)


@pytest.mark.parametrize(
    "msg_type,kwargs",
    [
        (MSG_PING, {}),
        (MSG_TASK, {"id": "t1", "action": "ping"}),
        (MSG_REGISTER, {"hostname": "host", "platform": "linux"}),
    ],
)
def test_make_parse_roundtrip(msg_type, kwargs):
    data = make_msg(msg_type, **kwargs)
    parsed = parse_msg(data)
    assert parsed["type"] == msg_type
    for k, v in kwargs.items():
        assert parsed[k] == v


def _loopback_server(port, received, ready_event, response_fn=None):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(1)
    ready_event.set()
    conn, _ = srv.accept()
    proto = ControlProtocol(conn)
    msg = proto.recv()
    received.append(msg)
    if response_fn:
        response_fn(proto)
    conn.close()
    srv.close()


def test_control_protocol_send_recv():
    port = CTRL_PORT_DEFAULT + 9999
    received = []
    ready = threading.Event()
    t = threading.Thread(
        target=_loopback_server,
        args=(port, received, ready),
        daemon=True,
    )
    t.start()
    ready.wait(2)
    proto = ControlProtocol()
    proto.connect("127.0.0.1", port, timeout=2)
    proto.send(MSG_PING)
    proto.recv()
    proto.send(MSG_DISCONNECT)
    proto.close()
    assert received and received[0]["type"] == MSG_PING
    t.join(timeout=2)


def test_register_ack_exchange():
    port = CTRL_PORT_DEFAULT + 9998
    received = []

    def respond(p):
        p.send(MSG_REGISTER_ACK, worker_id="w1", status="active")

    ready = threading.Event()
    t = threading.Thread(
        target=_loopback_server,
        args=(port, received, ready, respond),
        daemon=True,
    )
    t.start()
    ready.wait(2)
    proto = ControlProtocol()
    proto.connect("127.0.0.1", port, timeout=2)
    proto.send(MSG_REGISTER, hostname="host", platform="linux", rpc_port=50052)
    resp = proto.recv()
    proto.close()
    assert resp and resp["type"] == MSG_REGISTER_ACK
    assert resp["status"] == "active"
    assert resp["worker_id"] == "w1"
    t.join(timeout=2)
