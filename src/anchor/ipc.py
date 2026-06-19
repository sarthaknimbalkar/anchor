import hashlib
import os
import secrets
import sys


def state_dir(home: str) -> str:
    d = os.path.join(home, ".anchor")
    os.makedirs(d, mode=0o700, exist_ok=True)
    return d


def get_or_create_cookie(home: str) -> str:
    path = os.path.join(state_dir(home), "cookie")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            tok = f.read().strip()
        if tok:
            return tok
    tok = secrets.token_hex(32)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, tok.encode("utf-8"))
    finally:
        os.close(fd)
    return tok


def win_port_file(home: str) -> str:
    return os.path.join(state_dir(home), "anchord.port")


def socket_address(home: str) -> str:
    if sys.platform == "win32":
        h = hashlib.sha256(os.path.abspath(home).encode()).hexdigest()[:12]
        return rf"\\.\pipe\anchord-{h}"
    return os.path.join(state_dir(home), "anchord.sock")
