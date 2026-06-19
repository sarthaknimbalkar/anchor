from anchor.ruler import import_ruler, export_ruler
from anchor.rules import Rule, TIER_BLOCK


def test_import_makes_remind_rules():
    rules = import_ruler("# Rules\n- Always write tests\n- Prefer small PRs\n")
    assert len(rules) == 2
    assert all(r["tier"] == "remind" for r in rules)
    assert rules[0]["text"] == "Always write tests"


def test_export_renders_bullets():
    out = export_ruler([Rule(id="a", tier=TIER_BLOCK, text="Never force-push.")])
    assert "- Never force-push." in out
