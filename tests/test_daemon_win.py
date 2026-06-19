import sys
import threading
import time
import pytest
from anchor import daemon, client, guard
from anchor.rules import Rule, TIER_BLOCK
from anchor.compile import compile_match
from anchor.cache import index_by_tool


@pytest.mark.skipif(sys.platform != "win32", reason="Windows TCP-loopback server path")
def test_windows_daemon_serves(monkeypatch, tmp_path):
    rule = Rule(id="env", tier=TIER_BLOCK, text="no env", match=compile_match({"protects_paths": ["**/.env"]}))
    monkeypatch.setattr(guard, "_index_for", lambda cwd: index_by_tool([rule]))
    home = str(tmp_path)
    t = threading.Thread(target=daemon.run, kwargs={"home": home, "max_requests": 1}, daemon=True)
    t.start()
    time.sleep(0.3)
    call = {"tool_name": "Edit", "tool_input": {"file_path": "/p/.env"}, "cwd": "/p"}
    out = client.decide(call, home=home)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
