from anchor.rules import Rule, TIER_BLOCK, TIER_REMIND
from anchor.budget import select, est_tokens


def r(id, tier, text):
    return Rule(id=id, tier=tier, text=text)


def test_remind_rules_prioritized_over_blocks_when_budget_tight():
    # Re-injection is the ONLY enforcement remind rules have; block rules are
    # enforced by the guard regardless. So under a tight budget the remind wins
    # and the (already-enforced) block is dropped from injection.
    rules = [r("b1", TIER_BLOCK, "x" * 400), r("m1", TIER_REMIND, "keep me")]
    sel, _ = select(rules, budget_tokens=10)
    ids = {x.id for x in sel}
    assert "m1" in ids
    assert "b1" not in ids


def test_remind_rules_bounded_by_budget():
    rules = [r("b", TIER_BLOCK, "x" * 4), r("m1", TIER_REMIND, "a" * 40), r("m2", TIER_REMIND, "b" * 400)]
    sel, total = select(rules, budget_tokens=20)
    ids = {x.id for x in sel}
    assert "b" in ids and "m1" in ids and "m2" not in ids


def test_default_budget_injects_all_behavioral_rules():
    # Regression: a realistic constitution (several block + several remind rules)
    # must re-inject every behavioral remind rule at the default budget. The old
    # default (120) + block-first packing starved them out entirely.
    rules = [r(f"b{i}", TIER_BLOCK, "a block rule text") for i in range(6)] + [
        r(f"m{i}", TIER_REMIND, "a behavioral remind rule about doing things the right way")
        for i in range(7)
    ]
    sel, _ = select(rules)
    remind_ids = {x.id for x in sel if x.id.startswith("m")}
    assert len(remind_ids) == 7
