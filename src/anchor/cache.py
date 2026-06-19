import hashlib


def index_by_tool(block_rules) -> dict:
    idx: dict[str, list] = {}
    for r in block_rules:
        if not r.match:
            continue
        tools = r.match.get("tools") or ["*"]
        for t in tools:
            idx.setdefault(t, []).append(r)
    return idx


def candidates_for(index: dict, tool: str) -> list:
    return index.get(tool, []) + index.get("*", [])


def content_hash(paths: list[str]) -> str:
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(p.encode())
        try:
            with open(p, "rb") as f:
                h.update(f.read())
        except OSError:
            h.update(b"\x00<absent>")
    return h.hexdigest()
