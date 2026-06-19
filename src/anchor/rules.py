from dataclasses import dataclass

TIER_BLOCK = "block"
TIER_REMIND = "remind"
_TIERS = {TIER_BLOCK, TIER_REMIND}


class RuleError(ValueError):
    pass


@dataclass(frozen=True)
class Rule:
    id: str
    tier: str
    text: str
    category: str | None = None
    match: dict | None = None
    enabled: bool = True
    source_scope: str = "user"


def validate_rule(raw: dict, source_scope: str) -> Rule:
    rid = raw.get("id")
    if not rid or not isinstance(rid, str):
        raise RuleError("rule missing 'id' (string required)")
    tier = raw.get("tier")
    if tier not in _TIERS:
        raise RuleError(f"rule '{rid}': tier {tier!r} invalid (use 'block' or 'remind')")
    text = raw.get("text")
    if not text or not isinstance(text, str):
        raise RuleError(f"rule '{rid}': missing 'text' (string required)")
    return Rule(
        id=rid,
        tier=tier,
        text=text,
        category=raw.get("category"),
        enabled=bool(raw.get("enabled", True)),
        source_scope=source_scope,
    )
