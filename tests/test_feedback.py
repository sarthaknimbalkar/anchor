from anchor import feedback, guard
from anchor.rules import Rule, TIER_BLOCK
from anchor.compile import compile_match
from anchor.cache import index_by_tool


def test_build_emits_corrective_text(monkeypatch):
    rule = Rule(id="env", tier=TIER_BLOCK, text="Never edit env", match=compile_match({"protects_paths": ["**/.env"]}))
    monkeypatch.setattr(guard, "_index_for", lambda cwd: index_by_tool([rule]))
    msg = feedback.build({"tool_name": "Edit", "tool_input": {"file_path": "/p/.env"}, "cwd": "/p"})
    assert "rule 'env'" in msg and "compliant alternative" in msg


def test_build_empty_when_compliant(monkeypatch):
    monkeypatch.setattr(guard, "_index_for", lambda cwd: {})
    assert feedback.build({"tool_name": "Edit", "tool_input": {"file_path": "/p/ok.py"}, "cwd": "/p"}) == ""
