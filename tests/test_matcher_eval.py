from anchor.compile import compile_match
from anchor.matcher import rule_matches


def test_path_block_on_edit():
    m = compile_match({"protects_paths": ["**/.env"]})
    assert rule_matches(m, "Edit", {"file_path": "/p/.env"}, cwd="/p")
    assert not rule_matches(m, "Edit", {"file_path": "/p/main.py"}, cwd="/p")


def test_command_block_on_bash():
    m = compile_match({"blocks_command_containing": ["rm -rf"]})
    assert rule_matches(m, "Bash", {"command": "sudo rm -rf /tmp"}, cwd="/p")


def test_tool_not_in_scope_no_match():
    m = compile_match({"blocks_command_containing": ["rm -rf"]})  # tools=['Bash']
    assert not rule_matches(m, "Read", {"file_path": "rm -rf"}, cwd="/p")


def test_bare_existing_dir_token_is_caught(tmp_path, monkeypatch):
    # Regression: `rm -rf secret_data` (bare dir name, no slash) must be caught when the
    # directory exists under cwd. Previously evaded because the token lacked '/' or '.'.
    (tmp_path / "secret_data").mkdir()
    from anchor.matcher import rule_matches
    m = compile_match({"protects_paths": ["**/secret_data", "**/secret_data/**"]})
    cwd = str(tmp_path).replace("\\", "/")
    assert rule_matches(m, "Bash", {"command": "rm -rf secret_data"}, cwd)
    # a bare token that does NOT exist is not treated as a path (no over-block)
    assert not rule_matches(m, "Bash", {"command": "npm run build"}, cwd)


def test_read_of_protected_file_is_blocked():
    # Regression: reading a protected secret must be caught (exfiltration vector).
    from anchor.matcher import rule_matches
    m = compile_match({"protects_paths": ["**/.env"]})
    assert rule_matches(m, "Read", {"file_path": "/p/.env"}, "/p")
    assert not rule_matches(m, "Read", {"file_path": "/p/readme.md"}, "/p")
