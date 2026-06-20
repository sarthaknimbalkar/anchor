import os
import pytest
from anchor import control, guard
from anchor.rules import Rule, TIER_BLOCK


def test_parse_duration_units():
    assert control.parse_duration("45s") == 45
    assert control.parse_duration("30m") == 1800
    assert control.parse_duration("2h") == 7200
    assert control.parse_duration("1d") == 86400
    assert control.parse_duration("90") == 90  # bare number = seconds


def test_parse_duration_rejects_nonpositive():
    for bad in ("", "0", "-5m"):
        with pytest.raises(ValueError):
            control.parse_duration(bad)


def test_pause_resume_roundtrip(tmp_path):
    home = str(tmp_path)
    assert control.pause_remaining(home) == 0.0
    control.pause(home, 100, now=1000.0)
    # at now=1050 there should be ~50s left
    assert 49 <= control.pause_remaining(home, now=1050.0) <= 51
    control.resume(home)
    assert control.pause_remaining(home) == 0.0


def test_expired_pause_is_not_disabled(tmp_path):
    home = str(tmp_path)
    control.pause(home, 10, now=1000.0)
    assert control.enforcement_disabled(home, {}, now=2000.0) is False


def test_active_pause_disables(tmp_path):
    home = str(tmp_path)
    control.pause(home, 100, now=1000.0)
    assert control.enforcement_disabled(home, {}, now=1050.0) is True


def test_corrupt_pause_file_fails_safe(tmp_path):
    home = str(tmp_path)
    os.makedirs(os.path.join(home, ".anchor"), exist_ok=True)
    with open(os.path.join(home, ".anchor", "pause"), "w") as f:
        f.write("not-a-number")
    # Corrupt state must NOT disable a security control.
    assert control.enforcement_disabled(home, {}) is False


def test_env_kill_switch(tmp_path):
    assert control.enforcement_disabled(str(tmp_path), {"ANCHOR_DISABLE": "1"}) is True


def test_disabled_rule_ids():
    assert control.disabled_rule_ids({"ANCHOR_DISABLE_RULE": "a, b ,c"}) == {"a", "b", "c"}
    assert control.disabled_rule_ids({}) == set()


def _block_index():
    import re

    rule = Rule(
        id="no-x",
        tier=TIER_BLOCK,
        text="no x",
        match={
            "tools": ["Bash"],
            "path_globs": [],
            "command_res": [re.compile("danger")],
            "input_specs": [],
        },
    )
    return {"Bash": [rule]}


def test_guard_blocks_normally(monkeypatch):
    monkeypatch.setattr(guard, "_index_for", lambda cwd: _block_index())
    monkeypatch.delenv("ANCHOR_DISABLE", raising=False)
    monkeypatch.delenv("ANCHOR_DISABLE_RULE", raising=False)
    out = guard.evaluate({"tool_name": "Bash", "tool_input": {"command": "danger"}, "cwd": "."})
    assert out  # blocked


def test_guard_respects_env_kill_switch(monkeypatch):
    monkeypatch.setattr(guard, "_index_for", lambda cwd: _block_index())
    monkeypatch.setenv("ANCHOR_DISABLE", "1")
    out = guard.evaluate({"tool_name": "Bash", "tool_input": {"command": "danger"}, "cwd": "."})
    assert out == {}  # disabled


def test_guard_respects_disable_rule(monkeypatch):
    monkeypatch.setattr(guard, "_index_for", lambda cwd: _block_index())
    monkeypatch.delenv("ANCHOR_DISABLE", raising=False)
    monkeypatch.setenv("ANCHOR_DISABLE_RULE", "no-x")
    out = guard.evaluate({"tool_name": "Bash", "tool_input": {"command": "danger"}, "cwd": "."})
    assert out == {}  # specific rule skipped
