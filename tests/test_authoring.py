import tomllib
from anchor.authoring import rule_from_answers, append_rule, rule_from_log_entry


def test_rule_from_answers_block_with_paths():
    r = rule_from_answers({"id": "env", "intent": "block", "text": "no env", "paths": ["**/.env"]})
    assert r["tier"] == "block" and r["protects_paths"] == ["**/.env"]


def test_append_creates_and_appends(tmp_path):
    p = tmp_path / ".anchor.toml"
    append_rule(str(p), {"id": "a", "tier": "remind", "text": "x"})
    append_rule(str(p), {"id": "b", "tier": "block", "text": "y", "protects_paths": ["**/.env"]})
    data = tomllib.loads(p.read_text())
    assert {r["id"] for r in data["rule"]} == {"a", "b"}


def test_rule_from_log_entry():
    r = rule_from_log_entry({"tool": "Bash", "input": {"command": "rm -rf /"}})
    assert r["tier"] == "block" and "rm -rf /" in r["blocks_command_containing"][0]
