from anchor.migrate import needs_migration, migrate_text, CURRENT_SCHEMA


def test_missing_schema_needs_migration():
    assert needs_migration('[[rule]]\nid="a"\ntier="block"\ntext="t"\n') is True


def test_current_schema_is_idempotent():
    text = f"schema = {CURRENT_SCHEMA}\n"
    assert needs_migration(text) is False
    assert migrate_text(text) == text


def test_migrate_adds_schema():
    out = migrate_text('[[rule]]\nid="a"\ntier="block"\ntext="t"\n')
    assert out.startswith("schema = 1")
