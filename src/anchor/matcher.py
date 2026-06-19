import os
import posixpath
import re
import threading

MAX_INPUT_LEN = 8192


class MatcherTimeout(Exception):
    pass


# Heuristic detector for catastrophic-backtracking patterns. This is the PRIMARY
# ReDoS defense: a thread-based runtime timeout cannot interrupt CPython's `re`
# engine because it holds the GIL for the whole match, so dangerous patterns must
# be rejected statically at lint/compile time instead.
_NESTED_QUANTIFIER = re.compile(r"\([^)]*[+*][^)]*\)\s*[+*]")          # (a+)+  (.*)*  (a+)*
_ALTERNATION_OVERLAP = re.compile(r"\([^)]*\|[^)]*\)\s*[+*]")          # (a|aa)+


def is_dangerous_regex(pattern_str: str) -> bool:
    return bool(
        _NESTED_QUANTIFIER.search(pattern_str)
        or _ALTERNATION_OVERLAP.search(pattern_str)
    )


def safe_search(pattern, text: str, *, timeout_s: float = 0.05) -> bool:
    text = text[:MAX_INPUT_LEN]
    result: dict = {}

    def run():
        try:
            result["ok"] = pattern.search(text) is not None
        except Exception as e:  # noqa: BLE001
            result["err"] = e

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(timeout_s)
    if t.is_alive():
        raise MatcherTimeout(f"regex exceeded {timeout_s}s")
    if "err" in result:
        raise result["err"]
    return result.get("ok", False)


def normalize_path(raw: str, cwd: str) -> str:
    raw = raw.replace("\\", "/")
    cwd = cwd.replace("\\", "/")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:/", raw):
        joined = raw
    else:
        joined = posixpath.join(cwd, raw)
    return posixpath.normpath(joined).replace("\\", "/")


def _glob_to_regex(pattern: str) -> str:
    out = ["^"]
    i = 0
    while i < len(pattern):
        if pattern[i:i + 2] == "**":
            out.append(".*")
            i += 2
            continue
        c = pattern[i]
        if c == "*":
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    out.append("$")
    return "".join(out)


def glob_matches(pattern: str, normalized_path: str, *, case_insensitive: bool) -> bool:
    flags = re.IGNORECASE if case_insensitive else 0
    return re.match(_glob_to_regex(pattern), normalized_path, flags) is not None


_SHELL_OPS = {"&&", "||", "|", ";", "&", ">", "<", ">>", "<<", "(", ")", "{", "}"}


def extract_paths(tool: str, tool_input: dict, cwd: str) -> list[str]:
    import shlex

    out: list[str] = []
    # Any tool that targets a file by path (Read, Edit, Write, NotebookEdit, MCP fs tools...).
    # Critically includes Read: protecting a secret must also stop it being read for exfiltration.
    for key in ("file_path", "notebook_path", "path"):
        if tool_input.get(key):
            out.append(tool_input[key])
    if tool == "Bash" and tool_input.get("command"):
        try:
            tokens = shlex.split(tool_input["command"])
        except ValueError:
            tokens = tool_input["command"].split()
        for t in tokens:
            if not t or t.startswith("-") or t in _SHELL_OPS:
                continue
            if "/" in t or "." in t:
                out.append(t)  # explicit path-like token
            elif os.path.exists(normalize_path(t, cwd)):
                out.append(t)  # bare token that is a real file/dir under cwd (e.g. `rm -rf secret_data`)
    normed = [normalize_path(p, cwd) for p in out]
    resolved = []
    for p in normed:
        try:
            resolved.append(os.path.realpath(p).replace("\\", "/"))
        except OSError:
            pass
    return list(dict.fromkeys(normed + resolved))


def _tool_in_scope(match: dict, tool: str) -> bool:
    tools = match.get("tools")
    return tools is None or "*" in tools or tool in tools


def rule_matches(match: dict, tool: str, tool_input: dict, cwd: str) -> bool:
    if not _tool_in_scope(match, tool):
        return False
    case_insensitive = True
    if match["path_globs"]:
        paths = extract_paths(tool, tool_input, cwd)
        for g in match["path_globs"]:
            if any(glob_matches(g, p, case_insensitive=case_insensitive) for p in paths):
                return True
    if match["command_res"] and tool == "Bash":
        cmd = tool_input.get("command", "")
        if any(safe_search(rx, cmd) for rx in match["command_res"]):
            return True
    for field, rx in match["input_specs"]:
        val = tool_input.get(field)
        if isinstance(val, str) and safe_search(rx, val):
            return True
    return False
