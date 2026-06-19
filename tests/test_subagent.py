from anchor import subagent, discovery, loader
from anchor.rules import Rule, TIER_BLOCK


def test_reassert_includes_header_and_rules(monkeypatch, tmp_path):
    monkeypatch.setattr(discovery, "discover_files", lambda cwd, home: [("x", "user")])
    monkeypatch.setattr(
        loader, "load_all_rules", lambda files, trusted: [Rule(id="a", tier=TIER_BLOCK, text="Never force-push.")]
    )
    out = subagent.reassert("/p", str(tmp_path))
    assert "re-asserting rules after sub-agent" in out
    assert "Never force-push." in out


def test_reassert_empty_when_no_rules(monkeypatch, tmp_path):
    monkeypatch.setattr(discovery, "discover_files", lambda cwd, home: [])
    monkeypatch.setattr(loader, "load_all_rules", lambda files, trusted: [])
    assert subagent.reassert("/p", str(tmp_path)) == ""
