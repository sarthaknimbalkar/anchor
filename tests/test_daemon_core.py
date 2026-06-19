from anchor.daemon import DecisionCache
from anchor import guard
from anchor.rules import Rule, TIER_BLOCK
from anchor.compile import compile_match
from anchor.cache import index_by_tool


def test_decide_matches_guard_evaluate(monkeypatch):
    rule = Rule(id="env", tier=TIER_BLOCK, text="no env", match=compile_match({"protects_paths": ["**/.env"]}))
    monkeypatch.setattr(guard, "_index_for", lambda cwd: index_by_tool([rule]))
    dc = DecisionCache()
    call = {"tool_name": "Edit", "tool_input": {"file_path": "/p/.env"}, "cwd": "/p"}
    assert dc.decide(call) == guard.evaluate(call)
    assert dc.decide(call)["hookSpecificOutput"]["permissionDecision"] == "deny"
