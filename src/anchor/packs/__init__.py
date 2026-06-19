import os


def load_pack(name: str) -> str:
    fname = name.replace("-", "_") + ".toml"
    path = os.path.join(os.path.dirname(__file__), fname)
    if not os.path.exists(path):
        raise FileNotFoundError(f"unknown pack: {name}")
    with open(path, encoding="utf-8") as f:
        return f.read()
