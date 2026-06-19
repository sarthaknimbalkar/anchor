import pytest
from anchor.protocol import (
    encode_request,
    decode_request,
    encode_response,
    decode_response,
)


def test_request_roundtrip_with_cookie():
    blob = encode_request("good", {"tool_name": "Edit"})
    assert decode_request(blob, "good") == {"tool_name": "Edit"}


def test_wrong_cookie_rejected():
    blob = encode_request("attacker", {"tool_name": "Edit"})
    with pytest.raises(PermissionError):
        decode_request(blob, "good")


def test_response_roundtrip():
    d = {"hookSpecificOutput": {"permissionDecision": "deny"}}
    assert decode_response(encode_response(d)) == d
