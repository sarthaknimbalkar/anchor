import sys
from anchor.budget import select


def render(rules, budget_tokens: int = 500) -> str:
    if not rules:
        return ""
    selected, _ = select(rules, budget_tokens)
    if not selected:
        return ""
    lines = ["[Anchor rules - these are binding; follow them exactly]"]
    lines += [f"- {r.text}" for r in selected]
    return "\n".join(lines) + "\n"


def main() -> None:
    try:
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
        import os
        from anchor import discovery, loader

        sys.stdin.read()  # consume hook payload (unused fields)
        home = os.path.expanduser("~")
        cwd = os.getcwd()
        files = discovery.discover_files(cwd, home)
        trust_store = os.path.join(home, ".anchor", "trust.json")
        trusted = any(discovery.is_trusted(p, trust_store) for p, s in files if s == "project")
        rules = loader.load_all_rules(files, trusted)
        sys.stdout.write(render(rules))
    except Exception:  # noqa: BLE001 - fail-open: never break the turn
        pass
    sys.exit(0)
