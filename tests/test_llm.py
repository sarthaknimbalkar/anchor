from anchor.llm import judge
from anchor.rules import Rule, TIER_BLOCK


def test_no_client_means_no_call():
    r = Rule(id="x", tier=TIER_BLOCK, text="no danger")
    assert judge(r, {"command": "anything"}, client=None) is False


def test_client_consulted_when_present():
    class FakeClient:
        def ambiguous_violation(self, text, tool_input):
            return "danger" in tool_input.get("command", "")

    r = Rule(id="x", tier=TIER_BLOCK, text="no danger")
    assert judge(r, {"command": "do danger"}, client=FakeClient()) is True
    assert judge(r, {"command": "safe"}, client=FakeClient()) is False


def test_client_error_fails_open():
    class Boom:
        def ambiguous_violation(self, text, tool_input):
            raise RuntimeError("api down")

    r = Rule(id="x", tier=TIER_BLOCK, text="t")
    assert judge(r, {"command": "x"}, client=Boom()) is False
