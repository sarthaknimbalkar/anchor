# Anchor - Design Spec

_Date: 2026-06-18 | Status: approved design, pre-implementation | v2 (post triple-review)_

> **The wedge:** *Your AI agent recalls a rule with ~97% accuracy and breaks it anyway up to
> 99% of the time. CLAUDE.md is advisory. Anchor is enforcement - the only thing that actually
> stops it.* Guardrails for YOLO mode.

## 1. What it is

**Anchor** is a drop-in rule enforcer for Claude Code. You declare your rules once, per project;
Anchor deterministically re-injects the critical ones on every turn and **blocks tool calls that
violate hard constraints** - solving instruction drift without burning tokens, with no network
and no telemetry.

**The insight:** `CLAUDE.md` and memory are *advisory* - the model follows them by choice, so
they drift as context grows. Anchor moves enforcement into the **harness layer (hooks)**, which
runs deterministically regardless of what the model decides.

**Why two layers (re-injection AND blocking) - the KBV reframe.** Research (DriftBench,
arXiv 2604.28031) shows the dominant failure is *not* forgetting: models recall a constraint with
~97% accuracy and **still violate it in the same turn** (up to 99% on Sonnet 4.6). This
"Knows-But-Violates" (KBV) effect proves re-injection alone is structurally insufficient. Anchor's
two layers target two *distinct* failure modes:
- **Re-injection** counters slow context-dilution / lost-in-the-middle drift.
- **Deterministic blocking** is the *only* mechanism shown to stop KBV violations.

**Hero scenario:** users in **bypass permissions ("YOLO mode")** have *zero* harness guardrails -
Anchor's `PreToolUse` block is the only thing between the agent and a violation, so blocking must
be airtight. Permission-mode users benefit equally (block fires before the prompt + reminders).

### Guarantees (the contract)
1. **Never drifts** - hard constraints re-stated every turn, placed at end-of-context (recency).
2. **Never wastes tokens** - tight per-turn budget; deterministic matching = zero LLM calls by default.
3. **Never bleeds across projects** - rules scoped per-project *and per-target-path*.
4. **Never phones home** - zero network, zero telemetry in the core; only the opt-in LLM engine
   ever makes an outbound call. Local, offline, inspectable.
5. **Never disarmed by untrusted input** - a cloned repo cannot weaken your safety, and the agent
   cannot disable its own guardrail (see section 6 Security).

## 2. Rules: authoring, file model & config cascade

### Authoring - plain-English first, regex as the escape hatch
Most developers will not write regex. The **default** authoring surface is declarative sugar that
compiles down to the same engine; raw regex is reserved for power users.

```toml
schema = 1

# Plain-English (the common case - no regex):
[[rule]]
id = "no-force-push"
tier = "block"                       # block | remind  (primary axis)
text = "Never force-push."
blocks_command_containing = ["git push --force", "git push -f"]

[[rule]]
id = "protect-prod-env"
tier = "block"
text = "Never edit prod env; real env lives in /etc/signalminer/app.env."
protects_paths = ["/etc/signalminer/**", "**/.env", "**/.env.*"]

[[rule]]
id = "reserved-ports"
tier = "block"
text = "Ports 8000/8001/8003 are reserved by CestusAI."
blocks_command_matching = "(?<![0-9])(8000|8001|8003)(?![0-9])"   # power-user regex escape hatch

# Reminder-only (no matcher):
[[rule]]
id = "workflow"
tier = "remind"
category = "workflow"                 # optional sub-tag for organization
text = "Use superpowers (brainstorming->plans->TDD), not gsd. Commit once per phase."
```

- **Primary axis: `tier = "block" | "remind"`** (two behaviors, two names - not four). `block` =
  always-injected *and* blocks matching calls; `remind` = injected by relevance/budget only.
  Optional `category` (`workflow`/`style`/`fact`) organizes reminders without adding behavior.
- Sugar keys (`protects_paths`, `blocks_command_containing`, `blocks_command_matching`,
  `blocks_input`) compile to the matcher engine at cache-build time (cold path) - **zero hot-path cost.**
- A rule blocks only if it has a matcher; otherwise it's a pure reminder.
- `enabled = false` disables an inherited rule by `id` - **honored only from user scope** (see trust below).

### Config cascade + trust model
Discovered by walking up from the tool call's **target path** (not just cwd), merged by precedence:
1. `~/.anchor/global.toml` - your cross-project rules (user scope, fully trusted)
2. `~/.anchor/<...>` + `<project>/.anchor.local.toml` - gitignored, user-authored (trusted)
3. `<project>/.anchor.toml` - committed, **may ship in a cloned repo (untrusted until trusted)**

**Asymmetric precedence (security-critical).** A project `.anchor.toml` may **add** rules and
**strengthen** (raise a rule to `block`), but may **never weaken**: `enabled = false`,
tier-downgrade, redaction-off, and budget changes on an inherited `id` are **ignored from project
scope**. Only user scope can weaken/disable. This stops a cloned repo from disarming your guardrails.

**Trust-on-first-use.** A project `.anchor.toml` is **inert until `anchor trust`** (VS Code
Workspace-Trust style). Untrusted -> only your user-scope rules apply. Anchor stores a content hash
and re-prompts on change. `anchor list` shows *which layer* contributed/overrode each rule.

### Matcher model & cross-platform
- `match.tool` accepts any tool name incl. MCP (`mcp__*`) and **capability wildcards** (`tool = ["*"]`
  for "any tool"); a built-in field-extraction map knows where each known tool carries its path.
  `doctor` warns when active MCP tools aren't covered by any block rule.
- Matchers: `command` (regex over command), `path` (forward-slash globs; canonicalized - see section 6 C3),
  `input` (`{field, pattern}` over input JSON). AND-combined.
- **OS-independent paths:** globs always forward-slash; targets resolved to absolute, normalized,
  forward-slashed, symlink-resolved paths; case-insensitive on Win/macOS, case-sensitive on Linux.
- **Pure-Python, dependency-light.** Stdlib-only core. Token counting char/4 by default.
- **Duplicate `id` in one file = lint error.** Injection order is a stable sort (tier, id) -> deterministic.

## 3. Hooks, the hot path & performance ("absolute beast")

Four hooks (`anchor init` merges them into `settings.json`):

| Hook | Fires | Job |
|---|---|---|
| `UserPromptSubmit` | every prompt | Inject tiered reminders (block-tier always + budgeted reminders), placed **last** (recency). |
| `PreToolUse` | every tool call | Evaluate block matchers -> block via documented **JSON protocol** (`hookSpecificOutput.permissionDecision="deny"` + reason), `exit 2`+stderr as legacy fallback. |
| `PostToolUse` | after a tool runs | On a block/soft-violation, emit **corrective feedback** ("do X instead") to fix the *next* action. |
| `SubagentStop` | sub-agent returns | Re-assert rules after sub-agent ingestion to counter **inherited drift** (arXiv 2603.03258). |

### Two-tier performance architecture (both, no single point of failure)
**Tier A - lean fast-path (the foundation; always fast by construction):**
- **Minimal-import entrypoint:** the `guard` hook imports only stdlib + matcher + cache loader -
  never TOML parsing, CLI framework, or the LLM client. This alone slashes interpreter cost.
- **Precompiled cache:** TOML is parsed, cascade resolved, regexes compiled, and **matchers indexed
  by tool name**, then serialized to a cache file keyed by config **content-hash** (not mtime -
  see section 6 M4). Hot path = hash check -> load index. A `Read` call evaluates zero `Bash` matchers ->
  O(rules-for-this-tool), not O(all rules).
- **Async audit logging:** events buffered and flushed off the critical path; redaction never runs
  on the hot path. Default `metadata-only`; full redacted logging is lazy/opt-in.

**Tier B - `anchord` daemon (turbo layer, p95<5ms):**
- Long-lived local process holds the compiled index in memory, serves decisions over a Unix socket
  (POSIX) / named pipe (Windows). Hot-reloads on content-hash change.
- **Secure by construction (see section 6 C2):** socket in a `0700` dir, `0600` perms; daemon verifies
  peer UID (`SO_PEERCRED`/`LOCAL_PEERCRED`) / Windows owner-SID + `FILE_FLAG_FIRST_PIPE_INSTANCE`
  + restrictive DACL; a per-user random cookie both sides check; **no mutating commands over IPC**
  (rules only ever load from disk). An unverifiable daemon is treated as *down*.
- If the daemon is down/unverifiable, the hook **self-executes via Tier A** - identical decision,
  only latency degrades. The daemon is pure optimization; correctness never depends on it.

**Targets (measured, published by `bench perf`):** daemon path **p95 < 5ms**; lean fast-path
**p95 < 40ms** (after minimal-import + cache; interpreter-bound). Both reported, both gated in CI.

### Fail-safe matrix
| Failure | Behavior | Why |
|---|---|---|
| Reminder layer errors | **Fail-open**, session continues | Missing a reminder is annoying, not dangerous. |
| A block-rule matcher throws/times out | **Fail-closed for that rule's scope** + loud stderr | A safety rule that can't evaluate must assume danger. |
| Rules file malformed | **First-run grace mode: fail-OPEN with loud warning**, graduating to **fail-closed** once the user opts into strict | Sound long-term posture without a first-typo rage-uninstall. |
| Daemon down/unverifiable | Self-execute via Tier A | Daemon is optimization, not correctness. |
| User truly stuck | `anchor pause 30m` (file-based, user-only) / `ANCHOR_DISABLE_RULE=<id>` for *remind* tier only | Granular + time-boxed; **hard-rule disable is NOT honored from agent-settable env** (see section 6 H4). `doctor` warns loudly whenever any disable is active. |

## 4. CLI & token budget

| Command | Does |
|---|---|
| `anchor init [--pack <name>] [--dry-run]` | Atomically (temp+rename, locked) merges hooks into `settings.json` with the entrypoint pinned to an **absolute, user-scoped** path (never repo/PATH-relative - section 6 H3). `--dry-run` shows the exact diff first. Backs up, idempotent, never clobbers. Seeds `.anchor.toml` from a pack. |
| `anchor check "<prompt>" [--tool ... --path ...]` | **The demo command.** Dry-run: shows exactly what would be injected/blocked. (Was `test`.) |
| `anchor demo` | Runs a scripted violating call in a sandbox and shows the live block + feedback - the 60-second "aha". |
| `anchor trust` | Marks the current project's `.anchor.toml` as trusted (stores hash; re-prompts on change). |
| `anchor add [--from-log]` | Interactive/generative rule authoring; `--from-log` turns a logged action into a rule retroactively. |
| `anchor packs` | List/apply starter packs (`safe-yolo`, `python-prod`, `infra`, `commit-hygiene`); `packs/community/` is a contribution surface. |
| `anchor doctor` | Hooks wired? entrypoint pinned & valid? daemon healthy & verified? rules valid? any disable active (who set it)? CC hook-format version compatible? MCP tools covered? |
| `anchor uninstall` | Surgically removes only Anchor's hook entries (restores backup), stops the daemon. |
| `anchor migrate` | Upgrades rules files across `schema` versions with backup. |
| `anchor lint` / `list` / `log` / `pause` / `import-ruler` / `export-ruler` | Validate cascade (incl. ReDoS rejection section 6 H1); show effective rules + provenance; recent activity; time-boxed disable; [Ruler](https://github.com/intellectronica/ruler) (2.8k stars) interop. |
| `anchor bench perf` / `anchor bench drift` | See section 7. |

### Token budget
- Default **~120 tokens/turn** (research: ~80-token anchor restores adherence; larger worsens
  dilution - ContextEcho arXiv 2605.24279). Configurable.
- Order: all `block`-tier rules (never dropped) -> relevant `remind` rules by match signal until
  budget hit -> compress to one-liner -> drop. If block rules exceed budget they're all still
  injected and `lint` warns. Rules kept **verbatim, never summarized**; rule block protected from pruning.
- Every injection logs its token cost.

### Optional LLM engine (strictly opt-in, off by default)
Only `optional_llm = true` rules invoke it, only when deterministic matching is ambiguous; small
fast model + strict timeout; on timeout/error falls back to deterministic. Zero LLM calls unless
explicitly opted in (preserves Guarantee #2 and #4).

## 5. Project structure
```
anchor/
  config.py     # cascade discovery + TOML parse + schema validation + trust + path-scope resolution
  compile.py    # sugar->matcher compilation, cascade resolution, tool-name indexing, content-hash cache
  rules.py      # rule model, tier logic, enabled/override (asymmetric precedence), stable sort
  matcher.py    # PURE: (rule, tool, path, cmd) -> bool  [OS-normalized, symlink-resolved, ReDoS-safe]
  budget.py     # PURE: (rules, budget) -> selected set + token cost
  guard.py      # PreToolUse - minimal-import hot entrypoint (JSON block protocol + exit-2 fallback)
  inject.py     # UserPromptSubmit / SubagentStop (end-of-context placement)
  feedback.py   # PostToolUse corrective feedback
  daemon.py     # anchord: secure server (peer auth, cookie, no mutating IPC, hash hot-reload)
  client.py     # thin hook client -> daemon, self-execute fallback to Tier A
  redact.py     # gitleaks-grade secret detectors (PEM/JWT/prefix-tokens/conn-strings/Write content)
  audit.py      # async, concurrency-safe jsonl logging, rotation, 0600
  selfprotect.py# default rules guarding ~/.anchor, .anchor.toml, settings.json from the agent
  packs/        # bundled + community starter packs
  cli.py        # full cold-path CLI
tests/ benchmarks/ docs/
```

## 6. Security (promoted in-scope: malicious *repo* + normal user, not just malicious agent)

| ID | Sev | Issue | Fix |
|----|-----|-------|-----|
| C1 | Crit | Cloned repo's `.anchor.toml` disables your global safety | **Asymmetric precedence** (project can strengthen, never weaken) + **trust-on-first-use** (section 2) |
| C2 | Crit | Daemon socket has no peer auth -> spoof/poison | Peer UID/SID verify, `0600`+`0700`, anti-squat cookie, no mutating IPC, unverifiable=down (section 3 Tier B) |
| C3 | Crit | Symlink/redirection TOCTOU bypasses path matcher | Canonicalize (`realpath`) + match raw **and** resolved path; default pack blocks `ln -s`/redirection into protected globs; dial back over-promise |
| H1 | High | ReDoS from repo/user regex hangs hot path/daemon | Length cap + match timeout (watchdog) -> matcher-error/fail-closed; `lint` rejects nested unbounded quantifiers; strictest cap for untrusted scope; `re2` if available |
| H2 | High | Pattern redaction misses many secrets | gitleaks/detect-secrets-grade rules: PEM/SSH keys, JWT, prefix tokens (`ghp_`,`xoxb-`,`sk_live_`,`AIza`,`glpat-`), URL creds, `Authorization`/`-u`/`--password`; redact Write/Edit `content`; `metadata-only` default for YOLO |
| H3 | High | `init` settings.json merge: TOCTOU / entrypoint planting | Atomic temp+rename+lock; entrypoint pinned absolute user-scoped (never repo/PATH); `doctor` verifies it still points at the installed binary |
| H4 | High | `ANCHOR_DISABLE` env var is an agent-settable kill switch | Hard-rule disable honored **only** from user-only state file (`anchor pause`), never env; `PreToolUse` blocks Bash that sets `ANCHOR_DISABLE*` or edits Anchor config/state |
| M1 | Med | Agent can edit Anchor's own config/log | `selfprotect.py` ships default rules guarding `~/.anchor/`, `.anchor.toml(.local)`, `settings.json`; append-only audit with monotonic seq (truncation-detectable) |
| M2 | Med | MCP/new tools default-unguarded | Capability/wildcard tool match + field-extraction map; `doctor` coverage warning |
| M3 | Med | Audit log perms/growth/path leakage | `~/.anchor/` `0700`, log `0600`, size-capped rotation, `metadata-only` avoids input retention |
| M4 | Med | mtime-based reload spoofable/stale | Reload on **content hash** (not mtime); decreasing-strength reload treated per fail-closed |

## 7. Testing, benchmarking, docs, distribution

**Testing:** pure functions (`matcher`/`budget`/`redact`/compile/path-scope) -> golden tests; hooks ->
e2e sims feeding real CC hook JSON (JSON-protocol + exit-code fallback); **daemon-vs-fallback
behavioral parity** + daemon-down chaos test + **socket-auth/anti-squat security tests**; ReDoS
timeout test; trust-model test (untrusted repo can't weaken). CI matrix **Win+macOS+Linux** incl.
Windows UTF-8 stderr test.

**Benchmark - two tracks:**
1. **`bench perf`** - p50/p95/p99 for **both** daemon and lean fast-path, scaling 10/100/1000 rules
   (proving tool-indexing). Gates: daemon p95<5ms, fast-path p95<40ms. Real numbers published.
2. **`bench drift`** (the write-up centerpiece) - fork-probe harness (ContextEcho 2605.24279) +
   restatement/KBV metric (DriftBench 2604.28031) + restoring-force fit `deltaD=a+b-D`
   (Drift No More 2510.07777) + state-based GD (2505.02709). Outputs: adherence-vs-context-length
   chart + block-catch rate, Anchor vs baseline, bootstrap 95% CIs; LLM-judged + judge-free surfaces.

**Distribution:** `pipx install anchor-cli`; `anchor init --pack safe-yolo` is the headline.
Dependency-light core; `re2` optional.

**Docs - split by audience:** README = visceral (15-sec block GIF, the KBV one-liner,
60-sec quickstart via `anchor demo`, lead with privacy + `uninstall` + `--dry-run` trust story,
Ruler interop section). `BENCHMARKS.md` / blog = the academic rigor for the HN crowd. Every claim
backed by a runnable command.

## 8. Phased roadmap (full vision, buildable order - nothing cut)
- **v1.0 (core beast):** plain-English rules + cascade + trust model; `PreToolUse` block +
  `UserPromptSubmit` inject; Tier A lean fast-path + content-hash cache + tool-indexing; **all section 6
  security**; `safe-yolo` pack; `init/check/demo/trust/doctor/uninstall/lint/list/log/pause/add`;
  `bench perf`; async redacted logging.
- **v1.1 (turbo + depth):** `anchord` daemon (secure); `PostToolUse` feedback; `SubagentStop`;
  remaining packs + `packs/community`; `bench drift` + the published write-up.
- **v1.2 (reach):** Ruler import/export; generative `anchor add` (+`--from-log`); `migrate`;
  optional LLM engine.

## 9. Threat model (honest scope)
Anchor defends a **forgetful/drifting agent** *and* a **malicious repo against a normal user**
(C1/H4 promoted in-scope). It is **not** a sandbox or containment layer and cannot guarantee
defeat of a **maliciously evasive agent** (obfuscated shell, novel indirection) - path matching is
best-effort and documented as such. For untrusted code execution, use OS-level isolation. Anchor
raises the floor on rule adherence and closes the realistic gaps; it does not claim unbypassable
safety. This honesty is the product's credibility.
