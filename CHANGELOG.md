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

### Fixed (found by live dogfooding / code audit)
- **"Never bricked" guarantee was non-functional.** The enforcement path never honored any disable
  mechanism: `anchor pause` did not exist, `ANCHOR_DISABLE_RULE` was unimplemented, and `ANCHOR_DISABLE`
  was only *printed* by `doctor` while `guard.evaluate` still blocked. Added `anchor pause <30m|2h|…>` /
  `anchor resume`, a shared `control` chokepoint honored by both the daemon and the self-execute
  fallback, `ANCHOR_DISABLE` (kill switch) and `ANCHOR_DISABLE_RULE=id1,id2` (skip specific rules), with
  fail-safe semantics (a corrupt pause file never disables enforcement). `doctor` now reports true state.
- **Re-injection starved `remind` rules.** `budget.select` packed `block` rules first into a 120-token
  budget, so a realistic constitution's behavioral rules were dropped from injection entirely — even
  though block rules are already hard-enforced and need re-injection least. Reminders are now prioritized
  (block rules fill the remainder); default budget raised to 500.
- **Audit log was never written.** `audit.log_event` had no caller, so `~/.anchor/log.jsonl` never
  existed and `anchor add --from-log` always failed. Block decisions are now logged when opt-in
  `ANCHOR_AUDIT` is set (`metadata-only|redacted|full`; default `off`).
- Removed dead code in `daemon.py` (`_files_and_hash`, unused `DecisionCache` field, misleading
  "in-memory cache" docstring).
- `init` now pins an absolute interpreter path; a bare `anchor` command could silently fail to run
  (leaving the user unprotected) when the install dir wasn't on Claude Code's `PATH`.
- `rm -rf <bare-dir>` evasion - bare directory tokens that exist on disk are now treated as paths.
- `Read`->`Write` secret exfiltration - `file_path` is now extracted for all tools (incl. `Read`),
  so reading a protected secret is blocked.
- Recursive-delete rules hardened to catch all flag forms (`-r/-rf/-fr/-R/--recursive`).

### Notes
- No mandatory third-party runtime dependencies. No network, no telemetry in the core.
