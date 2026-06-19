def import_ruler(ruler_text: str) -> list[dict]:
    out = []
    n = 0
    for line in ruler_text.splitlines():
        s = line.strip()
        if s.startswith(("- ", "* ")):
            n += 1
            out.append({"id": f"ruler-{n}", "tier": "remind", "text": s[2:].strip()})
    return out


def export_ruler(rules) -> str:
    lines = ["# Rules (exported from Anchor)", ""]
    lines += [f"- {r.text}" for r in rules]
    return "\n".join(lines) + "\n"
