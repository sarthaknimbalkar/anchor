import pytest
from anchor.compile import compile_match
from anchor.rules import RuleError


def test_protects_paths_sugar():
    m = compile_match({"protects_paths": ["**/.env"]})
    assert m["path_globs"] == ["**/.env"]
    assert "Bash" in m["tools"] and "*" in m["tools"]


def test_blocks_command_containing_escapes():
    m = compile_match({"blocks_command_containing": ["git push --force"]})
    assert m["tools"] == ["Bash"]
    assert m["command_res"][0].search("git push --force now")


def test_no_matcher_returns_none():
    assert compile_match({}) is None


def test_dangerous_regex_rejected():
    with pytest.raises(RuleError, match="dangerous"):
        compile_match({"blocks_command_matching": r"(a+)+$"})
