# Anchor - Competitive Landscape & Research Findings

_Date: 2026-06-18 | Source: parallel research (GitHub/web tools survey + academic paper review)_

This doc preserves the evidence base for the design decisions and for the eventual Medium
write-up. Citations are load-bearing - verify before publication.

## 1. Competitive landscape

The space splits into two crowded-but-orthogonal clusters; Anchor occupies the empty middle.

### Security blockers (same mechanism, different goal - block universal dangerous ops)
| Tool | Stars | Mechanism | Notes |
|---|---|---|---|
| [rulebricks/claude-code-guardrails](https://github.com/rulebricks/claude-code-guardrails) | ~70 | PreToolUse -> Rulebricks cloud API allow/deny/ask | Cloud dependency |
| [dwarvesf/claude-guardrails](https://github.com/dwarvesf/claude-guardrails) | ~23 | Deny-rules + PreToolUse bash patterns + secret/injection scanners | Active, clean install/uninstall, lite/full profiles |
| [quilrai/AgentGuard](https://github.com/quilrai/AgentGuard) | ~26 | Local desktop app on :8008; DLP policies | **Fails open** when offline |
| mafiaguy/claude-security-guardrails | ~2 | PreToolUse/PostToolUse + SAFETY_LEVEL | Stale |

### Rule distributors (same config philosophy, NO enforcement)
| Tool | Stars | Notes |
|---|---|---|
| [intellectronica/ruler](https://github.com/intellectronica/ruler) | **2.8k** | `ruler.toml` -> generates per-agent config. Advisory only. Mindshare leader. |
| dyoshikawa/rulesync | mid | Centralizes rule files across agents. Distribution only. |

### Enterprise/commercial
- **Mneme** - constraints from prompt -> merge (CI gate). Closest in spirit but enterprise/cloud.
- **Cursor+Oasis**, **Corridor.dev** - identity/access governance, generation-time guardrails.

### Gaps nobody fills (= Anchor's seam)
1. No tool enforces the **user's own project rules** via *both* re-injection AND blocking.
2. Instruction drift is loudly felt (viral DEV posts: "I wrote 500 lines of rules... it ignored
   them all"); the folk-fix (UserPromptSubmit re-injection) is blog snippets, not a product.
3. Token cost of re-injection is universally ignored - our budget+tiering is differentiated.
4. No severity tiers mapping to different mechanisms (block vs remind).
5. No honest threat model; security tools over-promise.
6. No drift-efficacy benchmarking anywhere.

### Risks
- Anthropic could add native re-injection -> moat must be tiering + blocking + benchmarking.
- Ruler is the gravity well -> interop, don't compete on distribution.

## 2. Academic findings (the thesis upgrade)

**KBV - "Knows-But-Violates" (the key result).** DriftBench (arXiv 2604.28031): models recall
constraints at ~97% accuracy yet violate in the same turn - up to **99% (Sonnet 4.6)**. Rules out
forgetting as the mechanism. -> **Re-injection alone is insufficient; deterministic blocking is the
only thing shown to stop KBV.** This is Anchor's headline.

**Drift is fast & early.** 74% of drift cases show first violation by turn 2 (DriftBench). Benchmark
must probe early, not only late.

**Drift is bounded, self-correcting.** "Drift No More?" (arXiv 2510.07777): `deltaD = a + b-D`,
restoring slope b ~ -0.96 to -2.44 -> equilibrium, not runaway. Efficacy metric: does Anchor raise
|b| / lower D*?

**Lost-in-the-middle is architectural.** RoPE decay; mid-context instructions lose >30% attention
(arXiv 2510.10276). -> Inject rules at END (recency).

**~80 tokens is enough.** ContextEcho "A-Anchor" (arXiv 2605.24279): ~80-token anchor restored
adherence to ceiling; larger anchors worsen dilution. -> Tight budget by default.

**Inherited drift.** Sub-agent trajectories contaminate the parent (arXiv 2603.03258). -> Re-assert
on SubagentStop.

**Don't summarize rules.** Summarization is costly/lossy vs masking (arXiv 2508.21433). -> Keep
rules verbatim, protected from pruning.

**Don't trust self-reflection as a gate.** Reflection makes outputs *sound* compliant without being
compliant (DriftBench). -> Reflection = telemetry only, never the enforcement gate.

### Benchmark methodology (credible/publishable)
- Fork-probe harness (ContextEcho): fork at turn t, probe, discard; filler-control arm; drift gap.
- Restatement/KBV metric (DriftBench): restate-vs-comply gap = headline.
- Restoring-force fit (Drift No More): deltaD = a + b-D; show |b|, D*.
- State-based GD_actions / GD_inaction (arXiv 2505.02709), recovery-allowing.
- Report judged + judge-free deterministic fingerprint, bootstrap 95% CIs.

### Ideas folded into the spec
1. Inject at end of context (recency).
2. ~80-120 token budget (tight).
3. SubagentStop re-assertion (inherited drift).
4. PostToolUse corrective feedback.
5. Starter rule-packs / profiles.
6. Ruler interop (import/export).

## 3. Citations
- DriftBench - "Models Recall What They Violate" - arXiv:2604.28031
- ContextEcho - arXiv:2605.24279
- Drift No More? - arXiv:2510.07777
- Inherited Goal Drift - arXiv:2603.03258
- Nautilus Compass (black-box drift detection, ROC AUC 0.83) - arXiv:2605.09863
- Breaking Contextual Inertia (single-turn anchors) - arXiv:2603.04783
- The Complexity Trap (masking ~ summarization) - arXiv:2508.21433
- Lost in the Middle (architectural) - arXiv:2510.10276
- Goal Drift in Language Model Agents (GD metrics) - arXiv:2505.02709
- Reflection-Driven Control - arXiv:2512.21354
- LongGenBench (CR/STIC metrics) - ICLR 2025
- Zylos Research - Goal Persistence & Drift - https://zylos.ai/research/2026-04-03-goal-persistence-drift-long-horizon-ai-agents

_Note: several 2026 arXiv IDs were summarized by a small model during research; spot-check
PDF-only figures against source before publishing._
