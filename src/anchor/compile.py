import re
from anchor.rules import RuleError
from anchor.matcher import is_dangerous_regex

_DEFAULT_PATH_TOOLS = ["Edit", "Write", "Bash", "*"]


def _compile_re(pat: str, rid: str = "?") -> "re.Pattern":
    if is_dangerous_regex(pat):
        raise RuleError(f"rule '{rid}': dangerous regex {pat!r} (catastrophic backtracking risk)")
    try:
        return re.compile(pat)
    except re.error as e:
        raise RuleError(f"rule '{rid}': bad regex {pat!r}: {e}") from e


def compile_match(raw: dict) -> dict | None:
    rid = raw.get("id", "?")
    tools: set[str] = set()
    path_globs: list[str] = []
    command_res: list = []
    input_specs: list = []

    if "protects_paths" in raw:
        path_globs += list(raw["protects_paths"])
        tools.update(_DEFAULT_PATH_TOOLS)
    for s in raw.get("blocks_command_containing", []):
        command_res.append(_compile_re(re.escape(s), rid))
        tools.add("Bash")
    if "blocks_command_matching" in raw:
        command_res.append(_compile_re(raw["blocks_command_matching"], rid))
        tools.add("Bash")

    m = raw.get("match") or {}
    if "tool" in m:
        tools.update(m["tool"])
    if "path" in m:
        path_globs += list(m["path"])
        if not m.get("tool"):
            tools.update(_DEFAULT_PATH_TOOLS)
    if "command" in m:
        command_res.append(_compile_re(m["command"], rid))
        tools.add("Bash")
    if "input" in m:
        spec = m["input"]
        input_specs.append((spec["field"], _compile_re(spec["pattern"], rid)))

    if not (path_globs or command_res or input_specs):
        return None
    return {
        "tools": sorted(tools) if tools else None,
        "path_globs": path_globs,
        "command_res": command_res,
        "input_specs": input_specs,
    }
