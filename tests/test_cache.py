from anchor.rules import Rule, TIER_BLOCK
from anchor.cache import index_by_tool, candidates_for


def br(id, tools):
    return Rule(
        id=id,
        tier=TIER_BLOCK,
        text="t",
        match={"tools": tools, "path_globs": [], "command_res": [], "input_specs": []},
    )


def test_index_and_candidates():
    idx = index_by_tool([br("a", ["Bash"]), br("b", ["*"]), br("c", ["Edit"])])
    ids = lambda rs: sorted(r.id for r in rs)
    assert ids(candidates_for(idx, "Bash")) == ["a", "b"]
    assert ids(candidates_for(idx, "Read")) == ["b"]
