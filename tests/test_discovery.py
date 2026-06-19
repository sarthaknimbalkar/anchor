from anchor.discovery import is_trusted, trust


def test_trust_roundtrip(tmp_path):
    proj = tmp_path / ".anchor.toml"
    proj.write_text("schema=1\n")
    store = tmp_path / "trust.json"
    assert is_trusted(str(proj), str(store)) is False
    trust(str(proj), str(store))
    assert is_trusted(str(proj), str(store)) is True


def test_trust_invalidated_on_change(tmp_path):
    proj = tmp_path / ".anchor.toml"
    proj.write_text("schema=1\n")
    store = tmp_path / "trust.json"
    trust(str(proj), str(store))
    proj.write_text("schema=1\n# changed\n")
    assert is_trusted(str(proj), str(store)) is False
