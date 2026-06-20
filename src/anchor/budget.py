from anchor.rules import TIER_BLOCK


def est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def select(rules, budget_tokens: int = 500):
    """Choose which rules to re-inject, within a token budget.

    Re-injection is Anchor's *adherence* mechanism, and `remind` rules depend on
    it entirely — they have no other enforcement. `block` rules are already
    enforced deterministically by the guard, so re-injecting them is only a
    courtesy (it spares a wasted turn hitting a hard block). Therefore remind
    rules get the budget FIRST; block rules fill whatever room remains.

    Rules are kept in their given order within each tier, so callers control
    priority by ordering.
    """
    reminds = [r for r in rules if r.tier != TIER_BLOCK]
    blocks = [r for r in rules if r.tier == TIER_BLOCK]
    selected = []
    total = 0
    for r in reminds + blocks:
        cost = est_tokens(r.text)
        if total + cost <= budget_tokens:
            selected.append(r)
            total += cost
    return selected, total
