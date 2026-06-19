import pytest
from anchor.rules import validate_rule, Rule, RuleError, TIER_BLOCK


def test_valid_block_rule():
    r = validate_rule({"id": "x", "tier": "block", "text": "no"}, source_scope="user")
    assert r.id == "x" and r.tier == TIER_BLOCK and r.enabled is True


def test_unknown_tier_is_pointed_error():
    with pytest.raises(RuleError, match="tier 'hard' invalid"):
        validate_rule({"id": "x", "tier": "hard", "text": "t"}, source_scope="user")


def test_missing_text_errors():
    with pytest.raises(RuleError, match="missing 'text'"):
        validate_rule({"id": "x", "tier": "block"}, source_scope="user")
