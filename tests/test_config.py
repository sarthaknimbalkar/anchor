from anchor.rules import Rule, TIER_BLOCK, TIER_REMIND
from anchor.config import merge_cascade


def u(id, tier, enabled=True):
    return Rule(id=id, tier=tier, text="t", enabled=enabled, source_scope="user")


def p(id, tier, enabled=True):
    return Rule(id=id, tier=tier, text="t", enabled=enabled, source_scope="project")


def test_untrusted_project_rules_ignored():
    out = merge_cascade([u("a", TIER_BLOCK)], [p("b", TIER_BLOCK)], project_trusted=False)
    assert [r.id for r in out] == ["a"]


def test_project_cannot_disable_user_rule():
    out = merge_cascade([u("a", TIER_BLOCK)], [p("a", TIER_BLOCK, enabled=False)], project_trusted=True)
    assert out[0].enabled is True


def test_project_can_add_and_strengthen():
    out = merge_cascade([u("a", TIER_REMIND)], [p("a", TIER_BLOCK), p("c", TIER_BLOCK)], project_trusted=True)
    by = {r.id: r for r in out}
    assert by["a"].tier == TIER_BLOCK and "c" in by


def test_deterministic_sort():
    out = merge_cascade([u("z", TIER_REMIND), u("a", TIER_BLOCK)], [], True)
    assert [r.id for r in out] == ["a", "z"]
