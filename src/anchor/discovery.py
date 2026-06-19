import hashlib
import json
import os


def _hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def is_trusted(project_toml: str, trust_store: str) -> bool:
    if not os.path.exists(project_toml) or not os.path.exists(trust_store):
        return False
    try:
        store = json.loads(open(trust_store).read())
    except (OSError, ValueError):
        return False
    return store.get(os.path.abspath(project_toml)) == _hash(project_toml)


def trust(project_toml: str, trust_store: str) -> None:
    store = {}
    if os.path.exists(trust_store):
        try:
            store = json.loads(open(trust_store).read())
        except ValueError:
            store = {}
    store[os.path.abspath(project_toml)] = _hash(project_toml)
    os.makedirs(os.path.dirname(trust_store) or ".", mode=0o700, exist_ok=True)
    with open(trust_store, "w") as f:
        json.dump(store, f)


def discover_files(cwd: str, home: str):
    out = []
    g = os.path.join(home, ".anchor", "global.toml")
    if os.path.exists(g):
        out.append((g, "user"))
    d = os.path.abspath(cwd)
    while True:
        local = os.path.join(d, ".anchor.local.toml")
        proj = os.path.join(d, ".anchor.toml")
        if os.path.exists(local):
            out.append((local, "user"))
        if os.path.exists(proj):
            out.append((proj, "project"))
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return out
