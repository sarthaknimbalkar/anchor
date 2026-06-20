import os
import socket
import sys
from anchor import guard, ipc, protocol


class DecisionCache:
    def decide(self, hook_input: dict) -> dict:
        # Delegate to guard.evaluate so the daemon and the self-execute fallback
        # always reach an identical decision (including the kill-switch/pause and
        # ANCHOR_DISABLE_RULE handling inside guard.evaluate).
        return guard.evaluate(hook_input)


def serve_once(conn, cookie: str, dc: "DecisionCache") -> None:
    try:
        data = b""
        while not data.endswith(b"\n"):
            chunk = conn.recv(4096)
            if not chunk:
                return
            data += chunk
        hook_input = protocol.decode_request(data, cookie)
        decision = dc.decide(hook_input)
        conn.sendall(protocol.encode_response(decision))
    except Exception:  # noqa: BLE001 - never crash the daemon on one bad request
        pass
    finally:
        try:
            conn.close()
        except OSError:
            pass


def _run_tcp(home: str, cookie: str, dc: "DecisionCache", max_requests) -> None:
    # Windows has no portable stdlib named-pipe SERVER. We use a 127.0.0.1
    # loopback socket; the cookie (0600 file) is the authorization boundary,
    # since loopback is reachable by any local process. (spec section 6 C2 posture)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(16)
    port = srv.getsockname()[1]
    pf = ipc.win_port_file(home)
    fd = os.open(pf, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, str(port).encode())
    finally:
        os.close(fd)
    served = 0
    try:
        while max_requests is None or served < max_requests:
            conn, _ = srv.accept()
            serve_once(conn, cookie, dc)
            served += 1
    finally:
        srv.close()
        if os.path.exists(pf):
            os.unlink(pf)


def run(home: str | None = None, *, max_requests: int | None = None) -> None:
    home = home or os.path.expanduser("~")
    cookie = ipc.get_or_create_cookie(home)
    dc = DecisionCache()
    addr = ipc.socket_address(home)
    if sys.platform == "win32":
        _run_tcp(home, cookie, dc, max_requests)
        return
    if os.path.exists(addr):
        os.unlink(addr)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(addr)
    os.chmod(addr, 0o600)
    srv.listen(16)
    served = 0
    try:
        while max_requests is None or served < max_requests:
            conn, _ = srv.accept()
            serve_once(conn, cookie, dc)
            served += 1
    finally:
        srv.close()
        if os.path.exists(addr):
            os.unlink(addr)
