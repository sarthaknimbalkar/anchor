import re
from anchor.matcher import safe_search, MAX_INPUT_LEN, is_dangerous_regex


def test_normal_match():
    assert safe_search(re.compile(r"rm -rf"), "sudo rm -rf /") is True
    assert safe_search(re.compile(r"force"), "git push") is False


def test_input_is_length_capped():
    pat = re.compile("x")
    assert safe_search(pat, "y" * (MAX_INPUT_LEN + 100)) is False


def test_dangerous_regex_detected():
    # Nested unbounded quantifiers => catastrophic backtracking risk.
    assert is_dangerous_regex(r"(a+)+$") is True
    assert is_dangerous_regex(r"(.*)*") is True
    assert is_dangerous_regex(r"(a|aa)+$") is True


def test_safe_regex_allowed():
    assert is_dangerous_regex(r"rm -rf") is False
    assert is_dangerous_regex(r"(8000|8001|8003)") is False
    assert is_dangerous_regex(r"git push --force") is False
