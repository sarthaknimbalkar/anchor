def _s(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _list(values) -> str:
    return "[" + ", ".join(_s(v) for v in values) + "]"


def emit_rules(rules: list[dict]) -> str:
    out = ["schema = 1", ""]
    for r in rules:
        out.append("[[rule]]")
        for key in ("id", "tier", "text", "category"):
            if r.get(key) is not None:
                out.append(f"{key} = {_s(r[key])}")
        if "enabled" in r:
            out.append(f"enabled = {'true' if r['enabled'] else 'false'}")
        for key in ("protects_paths", "blocks_command_containing"):
            if key in r:
                out.append(f"{key} = {_list(r[key])}")
        out.append("")
    return "\n".join(out)
