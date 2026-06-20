import json
import os
import sys
from anchor import cache, control
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
    home = os.path.expanduser("~")
    # Kill-switch / time-boxed pause: a user can always disable enforcement
    # without uninstalling (the "never bricked" guarantee).
    if control.enforcement_disabled(home, os.environ):
        return {}
    tool = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {}) or {}
    cwd = hook_input.get("cwd", os.getcwd())
    index = _index_for(cwd)
    skip = control.disabled_rule_ids(os.environ)
    for rule in cache.candidates_for(index, tool):
        if rule.id in skip:
            continue
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


def _audit(hook_input: dict, decision: dict) -> None:
    # Opt-in local audit log. Default OFF (privacy-first; no telemetry ever).
    # ANCHOR_AUDIT = off | metadata-only | redacted | full
    #   metadata-only -> records the block without the tool input
    #   redacted      -> records input with secrets scrubbed
    #   full          -> records raw input (needed for `anchor add --from-log`)
    level = os.environ.get("ANCHOR_AUDIT", "off")
    if level == "off":
        return
    try:
        from anchor import audit

        audit.log_event(
            {
                "event": "block",
                "tool": hook_input.get("tool_name"),
                "input": hook_input.get("tool_input", {}),
                "reason": decision["hookSpecificOutput"]["permissionDecisionReason"],
            },
            log_path=os.path.join(os.path.expanduser("~"), ".anchor", "log.jsonl"),
            level=level,
        )
    except Exception:  # noqa: BLE001 - audit is best-effort, never break the hook
        pass


def main() -> None:
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    raw = sys.stdin.read() or "{}"
    from anchor import client  # lazy: keep module import graph lean
    hook_input = json.loads(raw)
    decision = client.decide(hook_input)
    if decision:
        _audit(hook_input, decision)
        print(json.dumps(decision))
        sys.stderr.write(decision["hookSpecificOutput"]["permissionDecisionReason"] + "\n")
        sys.exit(2)
    sys.exit(0)
