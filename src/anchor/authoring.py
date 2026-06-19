import os
from anchor.tomlemit import emit_rules
from anchor.rules import validate_rule
from anchor.compile import compile_match


def rule_from_answers(answers: dict) -> dict:
    rule = {
        "id": answers["id"],
        "tier": "block" if answers.get("intent") == "block" else "remind",
        "text": answers["text"],
    }
    if answers.get("paths"):
        rule["protects_paths"] = list(answers["paths"])
    if answers.get("commands"):
        rule["blocks_command_containing"] = list(answers["commands"])
    # validate by round-tripping through the real pipeline
    validate_rule(rule, "user")
    compile_match(rule)
    return rule


def append_rule(toml_path: str, rule: dict) -> None:
    existing = ""
    if os.path.exists(toml_path):
        with open(toml_path, encoding="utf-8") as f:
            existing = f.read()
    block = emit_rules([rule])
    if existing.strip():
        # strip the duplicate "schema = 1" header from the appended block
        body = block.split("\n", 2)[2] if block.startswith("schema") else block
        new = existing.rstrip() + "\n\n" + body.lstrip()
    else:
        new = block
    with open(toml_path, "w", encoding="utf-8") as f:
        f.write(new)


def rule_from_log_entry(entry: dict) -> dict:
    tool = entry.get("tool", "")
    inp = entry.get("input", {})
    rid = "from-log"
    if tool == "Bash" and inp.get("command"):
        return {
            "id": rid,
            "tier": "block",
            "text": "Blocked from log.",
            "blocks_command_containing": [inp["command"]],
        }
    if inp.get("file_path"):
        return {
            "id": rid,
            "tier": "block",
            "text": "Blocked from log.",
            "protects_paths": [inp["file_path"]],
        }
    return {"id": rid, "tier": "remind", "text": "Review this action."}
