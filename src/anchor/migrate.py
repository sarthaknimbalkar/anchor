import tomllib

CURRENT_SCHEMA = 1


def _schema_of(toml_text: str) -> int:
    try:
        return int(tomllib.loads(toml_text).get("schema", 0))
    except (tomllib.TOMLDecodeError, ValueError):
        return 0


def needs_migration(toml_text: str) -> bool:
    return _schema_of(toml_text) < CURRENT_SCHEMA


def migrate_text(toml_text: str) -> str:
    if not needs_migration(toml_text):
        return toml_text
    return f"schema = {CURRENT_SCHEMA}\n" + toml_text.lstrip()
