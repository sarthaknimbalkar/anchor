import os
import sys
from anchor import discovery, loader, inject


def reassert(cwd: str, home: str) -> str:
    files = discovery.discover_files(cwd, home)
    trust_store = os.path.join(home, ".anchor", "trust.json")
    trusted = any(discovery.is_trusted(p, trust_store) for p, s in files if s == "project")
    rules = loader.load_all_rules(files, trusted)
    body = inject.render(rules)
    if not body:
        return ""
    return "[Anchor - re-asserting rules after sub-agent output]\n" + body


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    try:
        sys.stdin.read()
        sys.stdout.write(reassert(os.getcwd(), os.path.expanduser("~")))
    except Exception:  # noqa: BLE001 - advisory, fail-open
        pass
    sys.exit(0)
