from anchor.redact import redact


def test_masks_common_secrets():
    assert "[redacted]" in redact("export API_KEY=sk_live_ABCDEF123456")
    assert "ghp_" not in redact("token ghp_0123456789abcdefghij0123456789abcd")
    assert "user:pass" not in redact("postgres://user:pass@host/db")


def test_keeps_innocuous_text():
    assert redact("git status") == "git status"
