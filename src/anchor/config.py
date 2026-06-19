import tomllib
from dataclasses import replace
from anchor.rules import Rule, validate_rule, RuleError, TIER_BLOCK, TIER_REMIND
from anchor.compile import compile_match

_TIER_ORDER = {TIER_BLOCK: 0, TIER_REMIND: 1}


def parse_file(path: str, source_scope: str) -> list[Rule]:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    seen: set[str] = set()
    rules: list[Rule] = []
    for raw in data.get("rule", []):
        r = validate_rule(raw, source_scope)
        if r.id in seen:
            raise RuleError(f"duplicate rule id {r.id!r} in {path}")
        seen.add(r.id)
        rules.append(replace(r, match=compile_match(raw)))
    return rules


def _is_stronger(new: Rule, old: Rule) -> bool:
    return _TIER_ORDER[new.tier] < _TIER_ORDER[old.tier]


def merge_cascade(user_rules, project_rules, project_trusted: bool) -> list[Rule]:
    by_id: dict[str, Rule] = {r.id: r for r in user_rules}
    if project_trusted:
        for pr in project_rules:
            if pr.id not in by_id:
                by_id[pr.id] = pr  # add
            elif _is_stronger(pr, by_id[pr.id]) and pr.enabled:
                by_id[pr.id] = replace(by_id[pr.id], tier=pr.tier, match=pr.match)  # strengthen only
            # weakening / disable from project scope: ignored
    out = [r for r in by_id.values() if r.enabled]
    out.sort(key=lambda r: (_TIER_ORDER[r.tier], r.id))
    return out
