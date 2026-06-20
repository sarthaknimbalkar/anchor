"""Enforcement kill-switch and time-boxed pause.

This backs the README's "never bricked" guarantee: a user can always disable
Anchor without uninstalling it.

Precedence (all checked in the enforcement path):
  - env ANCHOR_DISABLE       -> enforcement fully OFF (global kill switch)
  - ~/.anchor/pause          -> enforcement OFF until the stored expiry
  - env ANCHOR_DISABLE_RULE  -> comma-separated rule ids to skip

Fail-safe: a missing/corrupt pause file is ignored (enforcement stays ON), so
a damaged state file can never silently disable a security control.
"""
import os
import time

PAUSE_FILENAME = "pause"


def _pause_file(home: str) -> str:
    return os.path.join(home, ".anchor", PAUSE_FILENAME)


def parse_duration(s: str) -> int:
    """Parse '30m', '2h', '45s', '1d' (or a bare number of seconds) -> seconds."""
    s = (s or "").strip().lower()
    if not s:
        raise ValueError("empty duration")
    units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    if s[-1] in units:
        value = float(s[:-1])
        unit = units[s[-1]]
    else:
        value, unit = float(s), 1
    if value <= 0:
        raise ValueError(f"duration must be positive: {s!r}")
    return int(value * unit)


def pause(home: str, seconds: int, *, now: float | None = None) -> float:
    """Disable enforcement until now+seconds. Returns the expiry epoch."""
    until = (time.time() if now is None else now) + seconds
    d = os.path.join(home, ".anchor")
    os.makedirs(d, mode=0o700, exist_ok=True)
    fd = os.open(_pause_file(home), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, str(until).encode("utf-8"))
    finally:
        os.close(fd)
    return until


def resume(home: str) -> None:
    """Clear any active pause (no-op if not paused)."""
    try:
        os.unlink(_pause_file(home))
    except OSError:
        pass


def pause_remaining(home: str, *, now: float | None = None) -> float:
    """Seconds of pause left, or 0 if not paused / expired / corrupt."""
    path = _pause_file(home)
    if not os.path.exists(path):
        return 0.0
    try:
        with open(path, encoding="utf-8") as f:
            until = float(f.read().strip())
    except (OSError, ValueError):
        return 0.0  # fail-safe: corrupt file does not disable enforcement
    return max(0.0, until - (time.time() if now is None else now))


def enforcement_disabled(home: str, env: dict, *, now: float | None = None) -> bool:
    """True when enforcement should be skipped entirely (fail-open kill switch)."""
    if env.get("ANCHOR_DISABLE"):
        return True
    return pause_remaining(home, now=now) > 0


def disabled_rule_ids(env: dict) -> set:
    """Rule ids the user has opted to skip via ANCHOR_DISABLE_RULE=id1,id2."""
    raw = env.get("ANCHOR_DISABLE_RULE", "") or ""
    return {x.strip() for x in raw.split(",") if x.strip()}
