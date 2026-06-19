from anchor.rules import Rule, TIER_BLOCK
from anchor.compile import compile_match
from anchor import guard, cache


def _index(rules):
    return cache.index_by_tool(rules)


def test_blocks_matching_call(monkeypatch):
    rule = Rule(id="env", tier=TIER_BLOCK, text="no env", match=compile_match({"protects_paths": ["**/.env"]}))
    monkeypatch.setattr(guard, "_index_for", lambda cwd: _index([rule]))
    out = guard.evaluate({"tool_name": "Edit", "tool_input": {"file_path": "/p/.env"}, "cwd": "/p"})
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "no env" in out["hookSpecificOutput"]["permissionDecisionReason"]


def test_allows_nonmatching_call(monkeypatch):
    rule = Rule(id="env", tier=TIER_BLOCK, text="no env", match=compile_match({"protects_paths": ["**/.env"]}))
    monkeypatch.setattr(guard, "_index_for", lambda cwd: _index([rule]))
    assert guard.evaluate({"tool_name": "Edit", "tool_input": {"file_path": "/p/app.py"}, "cwd": "/p"}) == {}
