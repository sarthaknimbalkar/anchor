import threading


def judge(rule, tool_input: dict, *, client=None, timeout_s: float = 2.0) -> bool:
    if client is None:
        return False  # default: zero network, zero LLM calls (privacy contract)
    result = {"v": False}

    def run():
        try:
            result["v"] = bool(client.ambiguous_violation(rule.text, tool_input))
        except Exception:  # noqa: BLE001 - fail-open for relevance
            result["v"] = False

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(timeout_s)
    if t.is_alive():
        return False  # timeout => fail-open
    return result["v"]
