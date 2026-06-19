from anchor.rules import Rule, TIER_BLOCK, TIER_REMIND
from anchor.inject import render


def test_render_includes_block_rules_and_header():
    out = render([Rule(id="a", tier=TIER_BLOCK, text="Never force-push.")])
    assert "Never force-push." in out
    assert out.strip().startswith("[Anchor rules")


def test_render_empty_when_no_rules():
    assert render([]) == ""
