import io
import json
import sys
import anchor.guard as guard


def test_main_uses_client_decide(monkeypatch, capsys):
    captured = {}

    def fake_decide(hook_input, **kw):
        captured["seen"] = hook_input
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "blocked X",
            }
        }

    import anchor.client as client_mod
    monkeypatch.setattr(client_mod, "decide", fake_decide)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"tool_name": "Bash"})))
    code = None
    try:
        guard.main()
    except SystemExit as e:
        code = e.code
    assert code == 2
    assert captured["seen"]["tool_name"] == "Bash"
    assert "deny" in capsys.readouterr().out
