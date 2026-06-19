# Security & Threat Model

Anchor is a guardrail, not a sandbox. This document states precisely what it defends against -
overclaiming would be the fastest way to lose your trust.

## What Anchor defends against (in scope)

- **A forgetful or drifting agent.** The model loses track of a rule as context grows, or never
  internalized it, and attempts a straightforward violation. Caught deterministically.
- **A "Knows-But-Violates" agent.** The model can restate the rule yet violates it anyway. The
  `PreToolUse` block stops the action regardless of what the model "intends."
- **A malicious *repository* against a normal user.** A cloned repo's `.anchor.toml` cannot weaken
  or disable your global rules (asymmetric precedence), and is inert until you run `anchor trust`.
- **Path-targeted operations.** `protects_paths` matches the resolved target of any tool
  (`Read`/`Edit`/`Write`/`Bash`, incl. symlink resolution and bare directory names), so the agent
  cannot rephrase its way around protection of a specific file or directory.

## What Anchor does NOT defend against (out of scope)

- **A determined / adversarial agent.** An agent actively trying to achieve a forbidden outcome
  "by any means" can choose a tool or technique you did not anticipate (e.g. delete a directory
  file-by-file, or via a script). Command-pattern rules (`blocks_command_*`) are **best-effort**;
  path rules are robust but only for paths you name.
- **Untrusted code execution.** Anchor is not OS isolation. For running untrusted code, use a
  container, VM, or sandbox.
- **A compromised local machine.** Anchor's deterministic guarantees assume the daemon socket,
  cookie file, and config are not tampered with by other local processes you don't control.

## Hardening already in place

- **ReDoS protection** - user/repo regex is rejected at lint time if it has catastrophic-backtracking
  structure; matches run with a length cap.
- **Secret redaction** - the audit log redacts common secret patterns (keys, tokens, PEM, JWT, URL
  creds) before anything touches disk; default level is metadata-only.
- **Daemon authn** - `anchord` uses a per-user cookie over a `0600` socket / loopback; it never
  accepts mutating commands over IPC (rules load only from disk).
- **Pinned entrypoint** - `anchor init` writes an absolute interpreter path so the hook cannot be
  shadowed by `PATH`.

## Reporting a vulnerability

Open a private security advisory on the repository, or email the maintainer. Please do not file
public issues for exploitable findings until a fix is available.
