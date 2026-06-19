from anchor.daemon import DecisionCache
from anchor import guard
from anchor.rules import Rule, TIER_BLOCK
from anchor.compile import compile_match
from anchor.cache import index_by_tool


def test_daemon_and_fallback_decisions_identical(monkeypatch):
    rule = Rule(id="rm", tier=TIER_BLOCK, text="no rm", match=compile_match({"blocks_command_containing": ["rm -rf"]}))
    monkeypatch.setattr(guard, "_index_for", lambda cwd: index_by_tool([rule]))
    dc = DecisionCache()
    for call in [
        {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}, "cwd": "/p"},
        {"tool_name": "Bash", "tool_input": {"command": "ls"}, "cwd": "/p"},
        {"tool_name": "Read", "tool_input": {"file_path": "/p/x"}, "cwd": "/p"},
    ]:
        assert dc.decide(call) == guard.evaluate(call)
