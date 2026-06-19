from anchor.rules import TIER_BLOCK


def est_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def select(rules, budget_tokens: int = 120):
    blocks = [r for r in rules if r.tier == TIER_BLOCK]
    reminds = [r for r in rules if r.tier != TIER_BLOCK]
    selected = list(blocks)
    total = sum(est_tokens(r.text) for r in blocks)
    for r in reminds:
        cost = est_tokens(r.text)
        if total + cost <= budget_tokens:
            selected.append(r)
            total += cost
    return selected, total
