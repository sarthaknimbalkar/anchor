import json
import os
import sys
from anchor import cache
from anchor.matcher import rule_matches, MatcherTimeout


def _index_for(cwd: str) -> dict:
    from anchor import discovery, loader

    home = os.path.expanduser("~")
    files = discovery.discover_files(cwd, home)
    trust_store = os.path.join(home, ".anchor", "trust.json")
    project_trusted = any(
        discovery.is_trusted(p, trust_store) for p, s in files if s == "project"
    )
    return loader.load_block_index(files, project_trusted)


def evaluate(hook_input: dict) -> dict:
    tool = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {}) or {}
    cwd = hook_input.get("cwd", os.getcwd())
    index = _index_for(cwd)
    for rule in cache.candidates_for(index, tool):
        try:
            hit = rule_matches(rule.match, tool, tool_input, cwd)
        except MatcherTimeout:
            hit = True  # fail-closed for this block rule's scope
        if hit:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Anchor blocked (rule '{rule.id}'): {rule.text}",
                }
            }
    return {}


def main() -> None:
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raw = sys.stdin.read() or "{}"
    from anchor import client  # lazy: keep module import graph lean
    decision = client.decide(json.loads(raw))
    if decision:
        print(json.dumps(decision))
        sys.stderr.write(decision["hookSpecificOutput"]["permissionDecisionReason"] + "\n")
        sys.exit(2)
    sys.exit(0)
