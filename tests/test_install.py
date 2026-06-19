from anchor.install import merge_settings, remove_settings


def test_merge_is_idempotent_and_nonclobbering():
    base = {"hooks": {"PreToolUse": [{"hooks": [{"command": "other"}]}]}}
    once = merge_settings(base, "/abs/anchor")
    twice = merge_settings(once, "/abs/anchor")
    assert once == twice
    cmds = [h["command"] for grp in once["hooks"]["PreToolUse"] for h in grp["hooks"]]
    assert "other" in cmds and any("anchor" in c for c in cmds)


def test_remove_only_anchor():
    base = {"hooks": {"PreToolUse": [{"hooks": [{"command": "other"}]}]}}
    merged = merge_settings(base, "/abs/anchor")
    cleaned = remove_settings(merged)
    cmds = [h["command"] for grp in cleaned["hooks"].get("PreToolUse", []) for h in grp["hooks"]]
    assert "other" in cmds and not any("anchor" in c for c in cmds)
