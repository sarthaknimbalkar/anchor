# Example rule-packs

Copy any of these into your project as `.anchor.toml`, then run `anchor trust`.
Or apply directly at install: `anchor init --pack safe-yolo`.

| File | For |
|---|---|
| `safe-yolo.anchor.toml` | Running in `--dangerously-skip-permissions` - blocks destructive deletes, force-push, secret/env access, and edits to Anchor's own config. |
| `python-prod.anchor.toml` | Python projects - protects prod env, blocks system-wide pip installs, reminds to run tests. |
| `commit-hygiene.anchor.toml` | Git discipline - no force-push, no `--no-verify`, atomic commits. |

Rules are plain TOML - see the main [README](../README.md#writing-rules) for the format.
