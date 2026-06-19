# Contributing to Anchor

Thanks for considering a contribution. Anchor aims to be a small, dependency-light, rigorously
tested tool - contributions should keep it that way.

## Principles

- **Stdlib-only core.** No mandatory third-party runtime dependencies. Optional extras (e.g. `re2`)
  go behind `[project.optional-dependencies]`.
- **The hot path stays lean.** `guard.py` (PreToolUse) must import only stdlib + the matcher + the
  compiled rule index. Never add TOML parsing, the CLI, or the LLM client to it.
- **Pure functions, golden tests.** Matching/budget/redaction logic is pure and unit-tested. New
  behavior needs a test.
- **Honesty over marketing.** If something is best-effort, document it as best-effort.

## Dev setup

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"   # or .venv/bin/python on POSIX
.venv/Scripts/python -m pytest -q                  # full suite must be green
```

## Before opening a PR

1. `pytest -q` passes on your platform.
2. New rules-format / matcher behavior has a test.
3. If you touched enforcement, consider a scenario in `benchmarks/violation_bench.py`.
4. Run `anchor lint` on any new starter pack you add under `src/anchor/packs/`.

## Contributing a rule-pack

Drop a `<name>.toml` into `src/anchor/packs/community/` with a one-line description at the top. Packs
are plain Anchor rule files - see the README rule format.

## Commit style

Conventional-ish prefixes (`feat:`, `fix:`, `test:`, `docs:`). One logical change per commit.
