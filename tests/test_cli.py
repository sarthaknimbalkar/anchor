import json
from anchor.cli import main


def test_init_dry_run_writes_nothing(tmp_path, monkeypatch, capsys):
    settings = tmp_path / "settings.json"
    settings.write_text("{}")
    monkeypatch.setenv("ANCHOR_SETTINGS_PATH", str(settings))
    monkeypatch.setattr("shutil.which", lambda n: "/abs/anchor")
    rc = main(["init", "--dry-run"])
    assert rc == 0
    assert settings.read_text() == "{}"
    assert "PreToolUse" in capsys.readouterr().out


def test_init_then_uninstall_roundtrip(tmp_path, monkeypatch):
    settings = tmp_path / "settings.json"
    settings.write_text("{}")
    monkeypatch.setenv("ANCHOR_SETTINGS_PATH", str(settings))
    monkeypatch.setattr("shutil.which", lambda n: "/abs/anchor")
    assert main(["init"]) == 0
    assert "anchor" in settings.read_text()
    assert main(["uninstall"]) == 0
    data = json.loads(settings.read_text())
    assert not any(
        "anchor" in h.get("command", "")
        for grp in data.get("hooks", {}).get("PreToolUse", [])
        for h in grp["hooks"]
    )
