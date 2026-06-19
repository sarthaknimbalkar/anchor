from anchor.install import build_hook_config


def test_all_four_hooks_wired():
    cfg = build_hook_config("/abs/anchor")
    assert set(cfg) == {"PreToolUse", "UserPromptSubmit", "PostToolUse", "SubagentStop"}
    cmds = [h["command"] for grp in cfg["PostToolUse"] for h in grp["hooks"]]
    assert cmds == ["/abs/anchor feedback"]
