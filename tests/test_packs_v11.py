import tempfile
import os
import pytest
from anchor.packs import load_pack
from anchor.config import parse_file


@pytest.mark.parametrize("name", ["python-prod", "commit-hygiene"])
def test_pack_parses(name):
    text = load_pack(name)
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        rules = parse_file(path, "user")
    finally:
        os.unlink(path)
    assert len(rules) >= 1
