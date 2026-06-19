import os
import socket
import sys
from anchor import ipc, protocol, guard


def decide(hook_input: dict, *, home: str | None = None) -> dict:
    home = home or os.path.expanduser("~")
    try:
        cookie = ipc.get_or_create_cookie(home)
        addr = ipc.socket_address(home)
        if sys.platform == "win32":
            return _win_request(cookie, hook_input, home)
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.connect(addr)
        s.sendall(protocol.encode_request(cookie, hook_input))
        data = _recv_line(s)
        s.close()
        return protocol.decode_response(data)
    except Exception:  # noqa: BLE001 - any daemon failure => self-execute
        return guard.evaluate(hook_input)


def _recv_line(sock) -> bytes:
    buf = b""
    while not buf.endswith(b"\n"):
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    return buf


def _win_request(cookie: str, hook_input: dict, home: str) -> dict:
    pf = ipc.win_port_file(home)
    with open(pf) as f:
        port = int(f.read().strip())
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    s.connect(("127.0.0.1", port))
    s.sendall(protocol.encode_request(cookie, hook_input))
    data = _recv_line(s)
    s.close()
    return protocol.decode_response(data)
