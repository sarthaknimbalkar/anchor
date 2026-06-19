import json
import os
from anchor.redact import redact


def _redact_obj(o):
    if isinstance(o, str):
        return redact(o)
    if isinstance(o, dict):
        return {k: _redact_obj(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_redact_obj(v) for v in o]
    return o


def log_event(event: dict, *, log_path: str, level: str = "metadata-only") -> None:
    if level == "off":
        return
    rec = dict(event)
    if level == "metadata-only":
        rec.pop("input", None)
    elif level == "redacted":
        rec = _redact_obj(rec)
    d = os.path.dirname(log_path)
    if d:
        os.makedirs(d, mode=0o700, exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False) + "\n"
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)
