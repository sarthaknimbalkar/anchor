import tomllib
import tempfile
import os
from anchor.packs import load_pack
from anchor.config import parse_file


def test_safe_yolo_parses_and_has_block_rules():
    text = load_pack("safe-yolo")
    data = tomllib.loads(text)
    ids = {r["id"] for r in data["rule"]}
    assert {"no-rm-recursive", "protect-anchor-config"} <= ids
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        rules = parse_file(path, "user")
    finally:
        os.unlink(path)
    assert any(r.tier == "block" and r.match for r in rules)
