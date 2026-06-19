import tomllib
from anchor.cli import main


def test_add_writes_rule(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rc = main(["add", "--id", "env", "--block", "--text", "no env", "--path", "**/.env"])
    assert rc == 0
    data = tomllib.loads((tmp_path / ".anchor.toml").read_text())
    assert data["rule"][0]["id"] == "env" and data["rule"][0]["tier"] == "block"


def test_migrate_adds_schema_and_backs_up(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".anchor.toml").write_text('[[rule]]\nid="a"\ntier="block"\ntext="t"\n')
    rc = main(["migrate"])
    assert rc == 0
    assert (tmp_path / ".anchor.toml").read_text().startswith("schema = 1")
    assert (tmp_path / ".anchor.toml.bak").exists()
