import io
import json
import sys
import anchor.guard as guard
from anchor.rules import Rule, TIER_BLOCK
from anchor.compile import compile_match
from anchor.cache import index_by_tool


def test_guard_main_blocks_with_exit_2(monkeypatch, capsys):
    rule = Rule(id="env", tier=TIER_BLOCK, text="no env", match=compile_match({"protects_paths": ["**/.env"]}))
    monkeypatch.setattr(guard, "_index_for", lambda cwd: index_by_tool([rule]))
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "/p/.env"}, "cwd": "/p"})),
    )
    code = None
    try:
        guard.main()
    except SystemExit as e:
        code = e.code
    assert code == 2
    out = capsys.readouterr()
    assert "deny" in out.out and "no env" in out.err


def test_guard_main_allows_with_exit_0(monkeypatch):
    rule = Rule(id="env", tier=TIER_BLOCK, text="no env", match=compile_match({"protects_paths": ["**/.env"]}))
    monkeypatch.setattr(guard, "_index_for", lambda cwd: index_by_tool([rule]))
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "/p/ok.py"}, "cwd": "/p"})),
    )
    code = None
    try:
        guard.main()
    except SystemExit as e:
        code = e.code
    assert code == 0
