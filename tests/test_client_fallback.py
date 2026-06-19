from anchor import client, guard
from anchor.rules import Rule, TIER_BLOCK
from anchor.compile import compile_match
from anchor.cache import index_by_tool


def test_client_falls_back_when_no_daemon(monkeypatch, tmp_path):
    rule = Rule(id="env", tier=TIER_BLOCK, text="no env", match=compile_match({"protects_paths": ["**/.env"]}))
    monkeypatch.setattr(guard, "_index_for", lambda cwd: index_by_tool([rule]))
    call = {"tool_name": "Edit", "tool_input": {"file_path": "/p/.env"}, "cwd": "/p"}
    out = client.decide(call, home=str(tmp_path))
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
