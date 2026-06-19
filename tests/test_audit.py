import json
from anchor.audit import log_event


def test_metadata_only_drops_input(tmp_path):
    p = tmp_path / "log.jsonl"
    log_event(
        {"rule": "x", "decision": "deny", "input": {"command": "secret"}, "ts": "T"},
        log_path=str(p),
        level="metadata-only",
    )
    rec = json.loads(p.read_text().strip())
    assert "input" not in rec and rec["rule"] == "x"


def test_off_writes_nothing(tmp_path):
    p = tmp_path / "log.jsonl"
    log_event({"rule": "x", "ts": "T"}, log_path=str(p), level="off")
    assert not p.exists()


def test_redacted_masks(tmp_path):
    p = tmp_path / "log.jsonl"
    log_event(
        {"input": {"command": "API_KEY=sk_live_ABCDEF123456"}, "ts": "T"},
        log_path=str(p),
        level="redacted",
    )
    assert "sk_live_" not in p.read_text()
