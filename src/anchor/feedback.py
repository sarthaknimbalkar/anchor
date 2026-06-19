import json
import re
import sys
from anchor import guard


def build(hook_input: dict) -> str:
    decision = guard.evaluate(hook_input)
    if not decision:
        return ""
    reason = decision["hookSpecificOutput"]["permissionDecisionReason"]
    m = re.search(r"rule '([^']+)'\): (.*)", reason)
    if m:
        rid, text = m.group(1), m.group(2)
    else:
        rid, text = "?", reason
    return (
        f"Anchor: that action violates rule '{rid}' - {text} "
        f"Do not repeat it; choose a compliant alternative."
    )


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    try:
        raw = sys.stdin.read() or "{}"
        sys.stdout.write(build(json.loads(raw)))
    except Exception:  # noqa: BLE001 - advisory, fail-open
        pass
    sys.exit(0)
