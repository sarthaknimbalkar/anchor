import argparse
import json
import os
import shutil
import sys

from anchor import install, discovery, packs, loader, guard, inject
from anchor.rules import RuleError

# Windows consoles default to cp1252 and mangle non-ASCII (em-dash, []). Force UTF-8.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def _settings_path() -> str:
    return os.environ.get("ANCHOR_SETTINGS_PATH") or os.path.join(
        os.path.expanduser("~"), ".claude", "settings.json"
    )


def _read_settings(path: str) -> dict:
    if os.path.exists(path):
        try:
            return json.loads(open(path).read())
        except ValueError:
            return {}
    return {}


def _atomic_write(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def _trust_store() -> str:
    return os.path.join(os.path.expanduser("~"), ".anchor", "trust.json")


def _discover():
    return discovery.discover_files(os.getcwd(), os.path.expanduser("~"))


def _project_trusted(files) -> bool:
    store = _trust_store()
    return any(discovery.is_trusted(p, store) for p, s in files if s == "project")


def _entrypoint() -> str:
    # Pin to the absolute interpreter + module so the hook resolves regardless of PATH
    # (a bare "anchor" silently fails to run when the venv/pipx Scripts dir isn't on
    # Claude Code's PATH - which would leave the user UNPROTECTED). H3 fix.
    return f'"{sys.executable}" -m anchor'


def _cmd_init(args) -> int:
    entry = _entrypoint()
    path = _settings_path()
    existing = _read_settings(path)
    merged = install.merge_settings(existing, entry)
    if args.dry_run:
        print("PreToolUse + UserPromptSubmit hooks would be added:")
        print(json.dumps(merged.get("hooks", {}), indent=2))
        return 0
    if os.path.exists(path):
        shutil.copyfile(path, path + ".anchor-backup")
    _atomic_write(path, merged)
    if args.pack:
        proj = os.path.abspath(".anchor.toml")
        with open(proj, "w", encoding="utf-8") as f:
            f.write(packs.load_pack(args.pack))
        # The user authored this via init (not a cloned repo) - auto-trust it so it applies now.
        discovery.trust(proj, _trust_store())
        print(f"Wrote and trusted starter .anchor.toml from pack '{args.pack}'.")
    print(f"Anchor installed. Hooks wired in {path}.")
    return 0


def _cmd_uninstall(args) -> int:
    path = _settings_path()
    backup = path + ".anchor-backup"
    if os.path.exists(backup):
        shutil.copyfile(backup, path)
    else:
        _atomic_write(path, install.remove_settings(_read_settings(path)))
    print("Anchor uninstalled.")
    return 0


def _cmd_trust(args) -> int:
    proj = os.path.abspath(".anchor.toml")
    if not os.path.exists(proj):
        print("No .anchor.toml in current directory.", file=sys.stderr)
        return 1
    discovery.trust(proj, _trust_store())
    print(f"Trusted {proj}")
    return 0


def _cmd_lint(args) -> int:
    files = _discover()
    errors = 0
    for path, scope in files:
        try:
            from anchor import config

            config.parse_file(path, scope)
            print(f"OK   {path}")
        except RuleError as e:
            errors += 1
            print(f"FAIL {path}: {e}", file=sys.stderr)
    return 1 if errors else 0


def _cmd_list(args) -> int:
    files = _discover()
    rules = loader.load_all_rules(files, _project_trusted(files))
    if not rules:
        print("No effective rules.")
        return 0
    for r in rules:
        marker = "BLOCK" if r.tier == "block" else "remind"
        print(f"[{marker}] {r.id} ({r.source_scope}): {r.text}")
    return 0


def _cmd_check(args) -> int:
    files = _discover()
    rules = loader.load_all_rules(files, _project_trusted(files))
    print(inject.render(rules) or "(no rules would be injected)")
    if args.tool:
        hook_input = {"tool_name": args.tool, "tool_input": {}, "cwd": os.getcwd()}
        if args.path:
            hook_input["tool_input"]["file_path"] = args.path
        if args.command:
            hook_input["tool_input"]["command"] = args.command
        decision = guard.evaluate(hook_input)
        if decision:
            print("WOULD BLOCK: " + decision["hookSpecificOutput"]["permissionDecisionReason"])
        else:
            print(f"WOULD ALLOW: {args.tool}")
    return 0


def _cmd_doctor(args) -> int:
    path = _settings_path()
    settings = _read_settings(path)
    wired = any(
        h.get("command", "").endswith("guard")
        for grp in settings.get("hooks", {}).get("PreToolUse", [])
        for h in grp.get("hooks", [])
    )
    print(f"settings.json: {path}")
    print(f"  hooks wired: {'yes' if wired else 'NO - run anchor init'}")
    # Verify the actual wired command points at a real interpreter (not a bare PATH name).
    wired_cmd = ""
    for grp in settings.get("hooks", {}).get("PreToolUse", []):
        for h in grp.get("hooks", []):
            if "anchor" in h.get("command", ""):
                wired_cmd = h["command"]
    interp_ok = sys.executable and os.path.exists(sys.executable) and "-m anchor" in wired_cmd
    print(f"  wired command: {wired_cmd or '(none)'}")
    print(f"  entrypoint absolute & resolvable: {'yes' if interp_ok else 'NO - re-run anchor init to pin it'}")
    files = _discover()
    print(f"  rule files discovered: {len(files)}")
    print(f"  project trusted: {_project_trusted(files)}")
    if os.environ.get("ANCHOR_DISABLE"):
        print("  WARNING: ANCHOR_DISABLE is set - enforcement is OFF.")
    return 0


def _cmd_bench(args) -> int:
    from anchor import bench

    if args.kind == "drift":
        with open(args.with_file) as f:
            tw = json.load(f)
        with open(args.without_file) as f:
            two = json.load(f)
        out = bench.drift_adherence([], tw, two)
        print("Drift-reduction efficacy:")
        print(f"  adherence (Anchor):   {out['adherence_with']:.2%}")
        print(f"  adherence (baseline): {out['adherence_without']:.2%}")
        print(f"  block-catch rate:     {out['block_catch_rate']:.2%}")
        print(f"  delta:                {out['delta']:+.2%}")
        return 0

    files = _discover()
    rules = loader.load_all_rules(files, _project_trusted(files))
    from anchor.cache import index_by_tool

    idx = index_by_tool([r for r in rules if r.tier == "block"])
    out = bench.measure_guard(idx)
    print(f"PreToolUse guard latency (lean fast-path):")
    print(f"  p50: {out['p50_ms']:.3f} ms")
    print(f"  p95: {out['p95_ms']:.3f} ms   (gate: < 40 ms)")
    print(f"  p99: {out['p99_ms']:.3f} ms")
    return 0


def _cmd_add(args) -> int:
    from anchor import authoring

    proj = os.path.abspath(".anchor.toml")
    if args.from_log:
        log = os.path.join(os.path.expanduser("~"), ".anchor", "log.jsonl")
        last = None
        with open(log) as f:
            for line in f:
                last = json.loads(line)
        rule = authoring.rule_from_log_entry({"tool": last.get("tool"), "input": last.get("input", {})})
    else:
        rule = authoring.rule_from_answers({
            "id": args.id,
            "intent": "block" if args.block else "remind",
            "text": args.text,
            "paths": args.path or [],
            "commands": args.command or [],
        })
    authoring.append_rule(proj, rule)
    print(f"Added rule '{rule['id']}' to {proj}")
    return 0


def _cmd_import_ruler(args) -> int:
    from anchor import authoring, ruler

    with open(args.file, encoding="utf-8") as f:
        imported = ruler.import_ruler(f.read())
    proj = os.path.abspath(".anchor.toml")
    for r in imported:
        authoring.append_rule(proj, r)
    print(f"Imported {len(imported)} Ruler rules (as reminders) into {proj}")
    return 0


def _cmd_export_ruler(args) -> int:
    from anchor import ruler

    files = _discover()
    rules = loader.load_all_rules(files, _project_trusted(files))
    sys.stdout.write(ruler.export_ruler(rules))
    return 0


def _cmd_migrate(args) -> int:
    from anchor import migrate as _migrate

    proj = os.path.abspath(".anchor.toml")
    if not os.path.exists(proj):
        print("No .anchor.toml here.", file=sys.stderr)
        return 1
    text = open(proj, encoding="utf-8").read()
    if not _migrate.needs_migration(text):
        print("Already current schema.")
        return 0
    shutil.copyfile(proj, proj + ".bak")
    with open(proj, "w", encoding="utf-8") as f:
        f.write(_migrate.migrate_text(text))
    print("Migrated .anchor.toml (backup at .anchor.toml.bak)")
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    p = argparse.ArgumentParser(prog="anchor")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init")
    pi.add_argument("--pack")
    pi.add_argument("--dry-run", action="store_true")
    pi.set_defaults(fn=_cmd_init)

    sub.add_parser("uninstall").set_defaults(fn=_cmd_uninstall)
    sub.add_parser("trust").set_defaults(fn=_cmd_trust)
    sub.add_parser("lint").set_defaults(fn=_cmd_lint)
    sub.add_parser("list").set_defaults(fn=_cmd_list)
    sub.add_parser("doctor").set_defaults(fn=_cmd_doctor)

    pc = sub.add_parser("check")
    pc.add_argument("prompt", nargs="?", default="")
    pc.add_argument("--tool")
    pc.add_argument("--path")
    pc.add_argument("--command")
    pc.set_defaults(fn=_cmd_check)

    pb = sub.add_parser("bench")
    pb.add_argument("kind", choices=["perf", "drift"])
    pb.add_argument("--with-file")
    pb.add_argument("--without-file")
    pb.set_defaults(fn=_cmd_bench)

    sub.add_parser("guard").set_defaults(fn=lambda a: guard.main())
    sub.add_parser("inject").set_defaults(fn=lambda a: inject.main())

    from anchor import feedback as _feedback, subagent as _subagent, daemon as _daemon

    sub.add_parser("feedback").set_defaults(fn=lambda a: _feedback.main())
    sub.add_parser("subagent").set_defaults(fn=lambda a: _subagent.main())
    sub.add_parser("daemon").set_defaults(fn=lambda a: _daemon.run())

    pa = sub.add_parser("add")
    pa.add_argument("--id")
    pa.add_argument("--block", action="store_true")
    pa.add_argument("--text")
    pa.add_argument("--path", action="append")
    pa.add_argument("--command", action="append")
    pa.add_argument("--from-log", action="store_true")
    pa.set_defaults(fn=_cmd_add)

    pir = sub.add_parser("import-ruler")
    pir.add_argument("file")
    pir.set_defaults(fn=_cmd_import_ruler)

    sub.add_parser("export-ruler").set_defaults(fn=_cmd_export_ruler)
    sub.add_parser("migrate").set_defaults(fn=_cmd_migrate)

    args = p.parse_args(argv)
    return args.fn(args) or 0
