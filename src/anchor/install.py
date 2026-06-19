import copy

_EVENTS = {
    "PreToolUse": "guard",
    "UserPromptSubmit": "inject",
    "PostToolUse": "feedback",
    "SubagentStop": "subagent",
}


def build_hook_config(entrypoint: str) -> dict:
    hooks = {}
    for event, sub in _EVENTS.items():
        hooks[event] = [
            {"_anchor": True, "hooks": [{"type": "command", "command": f"{entrypoint} {sub}"}]}
        ]
    return hooks


def merge_settings(existing: dict, entrypoint: str) -> dict:
    out = copy.deepcopy(existing)
    out.setdefault("hooks", {})
    anchor_hooks = build_hook_config(entrypoint)
    for event, groups in anchor_hooks.items():
        current = [g for g in out["hooks"].get(event, []) if not g.get("_anchor")]
        out["hooks"][event] = current + groups
    return out


def remove_settings(existing: dict) -> dict:
    out = copy.deepcopy(existing)
    for event in list(out.get("hooks", {})):
        out["hooks"][event] = [g for g in out["hooks"][event] if not g.get("_anchor")]
        if not out["hooks"][event]:
            del out["hooks"][event]
    return out
