import hmac
import json


def encode_request(cookie: str, hook_input: dict) -> bytes:
    return (json.dumps({"cookie": cookie, "hook_input": hook_input}) + "\n").encode("utf-8")


def decode_request(data: bytes, expected_cookie: str) -> dict:
    obj = json.loads(data.decode("utf-8"))
    got = obj.get("cookie", "")
    if not hmac.compare_digest(str(got), str(expected_cookie)):
        raise PermissionError("anchord: cookie mismatch")
    hi = obj.get("hook_input")
    if not isinstance(hi, dict):
        raise ValueError("anchord: missing hook_input")
    return hi


def encode_response(decision: dict) -> bytes:
    return (json.dumps(decision) + "\n").encode("utf-8")


def decode_response(data: bytes) -> dict:
    return json.loads(data.decode("utf-8"))
