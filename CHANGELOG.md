# Changelog

All notable changes to Anchor. Format loosely follows [Keep a Changelog](https://keepachangelog.com).

## [Unreleased]

### Added
- **v1.0 core** - `PreToolUse` block + `UserPromptSubmit` re-injection; plain-English rules
  (`protects_paths`, `blocks_command_*`) with `block`/`remind` tiers; config cascade with
  trust-on-first-use and asymmetric precedence; tool-name-indexed compiled cache; `safe-yolo` pack;
  CLI (`init/check/trust/lint/list/doctor/uninstall/pause`); `bench perf`.
- **v1.1** - secure `anchord` daemon (cookie auth, self-execute fallback); `PostToolUse` corrective
  feedback; `SubagentStop` re-assertion; `python-prod` + `commit-hygiene` packs; `bench drift`.
- **v1.2** - Windows daemon (loopback + cookie); generative `anchor add` (+`--from-log`); Ruler
  import/export; `anchor migrate`; strictly opt-in LLM engine.
- **Benchmarks** - live violation-prevention 2x2 on the real Claude Code CLI (nominal + adversarial,
  Wilson 95% CIs) and a live instruction-drift study on local models.

### Fixed (found by live benchmarking)
- `init` now pins an absolute interpreter path; a bare `anchor` command could silently fail to run
  (leaving the user unprotected) when the install dir wasn't on Claude Code's `PATH`.
- `rm -rf <bare-dir>` evasion - bare directory tokens that exist on disk are now treated as paths.
- `Read`->`Write` secret exfiltration - `file_path` is now extracted for all tools (incl. `Read`),
  so reading a protected secret is blocked.
- Recursive-delete rules hardened to catch all flag forms (`-r/-rf/-fr/-R/--recursive`).

### Notes
- No mandatory third-party runtime dependencies. No network, no telemetry in the core.
