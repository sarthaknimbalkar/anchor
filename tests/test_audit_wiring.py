import json
import os
from anchor import guard

_DECISION = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Anchor blocked (rule 'no-x'): no x",
    }
}
_HOOK_INPUT = {"tool_name": "Bash", "tool_input": {"command": "danger"}}


def _log_path(home):
    return os.path.join(home, ".anchor", "log.jsonl")


def test_audit_off_by_default_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmp_path))
    monkeypatch.delenv("ANCHOR_AUDIT", raising=False)
    guard._audit(_HOOK_INPUT, _DECISION)
    assert not os.path.exists(_log_path(str(tmp_path)))


def test_audit_metadata_only_omits_input(tmp_path, monkeypatch):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmp_path))
    monkeypatch.setenv("ANCHOR_AUDIT", "metadata-only")
    guard._audit(_HOOK_INPUT, _DECISION)
    rec = json.loads(open(_log_path(str(tmp_path))).read().strip())
    assert rec["tool"] == "Bash"
    assert "input" not in rec


def test_audit_full_keeps_input_for_from_log(tmp_path, monkeypatch):
    monkeypatch.setattr(os.path, "expanduser", lambda p: str(tmp_path))
    monkeypatch.setenv("ANCHOR_AUDIT", "full")
    guard._audit(_HOOK_INPUT, _DECISION)
    rec = json.loads(open(_log_path(str(tmp_path))).read().strip())
    assert rec["input"]["command"] == "danger"
