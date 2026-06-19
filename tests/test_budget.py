from anchor.rules import Rule, TIER_BLOCK, TIER_REMIND
from anchor.budget import select, est_tokens


def r(id, tier, text):
    return Rule(id=id, tier=tier, text=text)


def test_block_rules_always_included_even_over_budget():
    rules = [r("b1", TIER_BLOCK, "x" * 1000), r("b2", TIER_BLOCK, "y" * 1000)]
    sel, _ = select(rules, budget_tokens=10)
    assert {x.id for x in sel} == {"b1", "b2"}


def test_remind_rules_bounded_by_budget():
    rules = [r("b", TIER_BLOCK, "x" * 4), r("m1", TIER_REMIND, "a" * 40), r("m2", TIER_REMIND, "b" * 400)]
    sel, total = select(rules, budget_tokens=20)
    ids = {x.id for x in sel}
    assert "b" in ids and "m1" in ids and "m2" not in ids
