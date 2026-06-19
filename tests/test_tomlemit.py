import tomllib
from anchor.tomlemit import emit_rules


def test_emit_roundtrips_through_tomllib():
    text = emit_rules([
        {"id": "a", "tier": "block", "text": 'No "force" push', "blocks_command_containing": ["git push -f"]},
        {"id": "b", "tier": "remind", "text": "Use TDD"},
    ])
    data = tomllib.loads(text)
    assert data["rule"][0]["id"] == "a"
    assert data["rule"][0]["text"] == 'No "force" push'
    assert data["rule"][0]["blocks_command_containing"] == ["git push -f"]
    assert data["rule"][1]["tier"] == "remind"
