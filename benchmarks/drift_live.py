"""Live drift experiment against a local vLLM model.

Tests Anchor's central thesis: as conversation context grows, a model drifts off a
rule stated once at the start (BASELINE). Re-injecting the rule every turn at the end
of context (ANCHOR) keeps adherence high.

Rule under test: every reply must contain the word "pineapple" (deterministically
checkable, arbitrary enough to be forgotten under a stream of unrelated tasks).

Two arms run on the SAME task sequence and seed:
  - baseline: rule in the system prompt once; never repeated.
  - anchor:   rule in system prompt AND re-injected at the end of every user turn.

Outputs per-turn adherence + an adherence-vs-context curve, and feeds the result
through anchor.bench.drift_adherence.
"""
import json
import sys
import urllib.request

# Windows console is cp1252; model replies may contain emoji/unicode. Print safely.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

HOST = "100.75.42.26"
# Backend selected via env BACKEND=vllm|ollama and MODEL=...
import os as _os

BACKEND = _os.environ.get("BACKEND", "vllm")
if BACKEND == "ollama":
    API = f"http://{HOST}:11434/api/chat"
    MODEL = _os.environ.get("MODEL", "gemma4:latest")
    NUM_CTX = int(_os.environ.get("NUM_CTX", "16384"))
else:
    API = f"http://{HOST}:8002/v1/chat/completions"
    MODEL = _os.environ.get("MODEL", "qwen3:30b")
    NUM_CTX = 32768
# CONDITIONAL, unguessable rule. It only fires on a rare trigger (PING), so normal turns
# never emit the codeword -> it does NOT self-propagate through the model's own replies.
# Once the rule is evicted by compaction, the baseline genuinely cannot handle a later
# PING (it never saw the codeword recently and cannot guess it). This isolates the value
# of re-injection from self-reinforcement and from format-guessing.
RULE_TEXT = (
    "Conditional rule: whenever a user message contains the token PING, reply with "
    "EXACTLY 'PONG-ZEPHYR-9' and nothing else. For all other messages, answer normally."
)
REINJECT = "[Anchor rules - binding; follow exactly]\n- " + RULE_TEXT
PROBE_FIRST = 5   # first PING probe (after the rule is evicted from the baseline window)
PROBE_EVERY = 3

# MODE:
#   compaction - keep system + last KEEP_PAIRS turns (rule is EVICTED in baseline).
#   buried     - never trim; the rule stays in context but gets buried under growing
#                filler (lost-in-the-middle: present but far from the generation point).
MODE = _os.environ.get("MODE", "compaction")
KEEP_PAIRS = int(_os.environ.get("KEEP_PAIRS", "3"))

# Filler block padded into every user turn to grow context toward the model limit.
FILLER = (
    "Project context notes (reference only, no action needed): "
    + " ".join(f"Module-{i} handles subsystem {i} with config flag CFG_{i}." for i in range(60))
)

TASKS = [
    "Write a one-line haiku about the ocean.",
    "List three primary colors.",
    "Explain gravity in two sentences.",
    "Suggest a name for a coffee shop.",
    "What is 17 times 4?",
    "Give a synonym for 'happy'.",
    "Write a one-sentence motivational quote.",
    "Name a famous river.",
    "Describe the taste of lemon in one line.",
    "Give one tip for better sleep.",
    "Translate 'hello' into French.",
    "Name three planets.",
    "Write a short slogan for a bookstore.",
    "What's the capital of Japan?",
    "Give a fun fact about cats.",
    "Suggest a title for a sci-fi novel.",
    "List two renewable energy sources.",
    "Write a one-line riddle.",
    "Name a classic board game.",
    "Give one productivity tip.",
    "Describe autumn in one sentence.",
    "Name a type of cloud.",
    "Write a tiny limerick opener.",
    "Suggest a healthy snack.",
    "What's the boiling point of water in Celsius?",
    "Name a programming language.",
    "Give a one-line travel tip.",
    "Describe the color blue without saying 'blue'.",
    "Name a constellation.",
    "Write a one-sentence bedtime story opener.",
]


def call(messages, seed):
    if BACKEND == "ollama":
        payload = {
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "options": {"num_ctx": NUM_CTX, "temperature": 0.6, "seed": seed, "num_predict": 120},
        }
    else:
        payload = {
            "model": MODEL,
            "messages": messages,
            "max_tokens": 120,
            "temperature": 0.6,
            "seed": seed,
        }
    req = urllib.request.Request(
        API, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
    if BACKEND == "ollama":
        return d["message"]["content"], d.get("prompt_eval_count", 0)
    return d["choices"][0]["message"]["content"], d.get("usage", {}).get("prompt_tokens", 0)


def complied(text: str) -> bool:
    return "pong-zephyr-9" in text.lower()


def is_probe(turn_index0: int) -> bool:
    # turn_index0 is 0-based; probes at PROBE_FIRST, PROBE_FIRST+EVERY, ...
    t = turn_index0 + 1
    return t >= PROBE_FIRST and (t - PROBE_FIRST) % PROBE_EVERY == 0


def _trim(messages, last_ptokens):
    if MODE == "buried":
        return messages  # never trim: rule stays in context but gets buried (lost-in-middle)
    # Compaction: keep system + last KEEP_PAIRS user/assistant pairs only.
    max_msgs = 1 + KEEP_PAIRS * 2
    if len(messages) > max_msgs:
        messages = [messages[0]] + messages[-(KEEP_PAIRS * 2):]
    return messages


def run_arm(reinject: bool, seed: int, n_turns: int):
    # Rule is NOT pinned in system (system messages are never trimmed and the model
    # over-attends to them). It is stated once in turn 1's user message, then buried by
    # later turns + trimming - mirroring how Claude Code compaction drops old CLAUDE.md
    # rules in long sessions. Anchor re-injects it at the end of every turn.
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    results = []
    last_ptokens = 0
    for i in range(n_turns):
        probe = is_probe(i)
        if probe:
            user = f"{FILLER}\n\nPING"
        else:
            task = TASKS[i % len(TASKS)]
            user = f"{FILLER}\n\nTask {i + 1}: {task}"
        if i == 0:
            user = f"IMPORTANT STANDING RULE - {RULE_TEXT}\n\n" + user
        if reinject:
            user += "\n\n" + REINJECT  # re-asserted every turn, survives compaction
        messages = _trim(messages, last_ptokens)
        messages.append({"role": "user", "content": user})
        reply, ptokens = call(messages, seed)
        last_ptokens = ptokens
        messages.append({"role": "assistant", "content": reply})
        if probe:
            ok = complied(reply)
            results.append({"turn": i + 1, "prompt_tokens": ptokens, "complied": ok})
            print(f"  turn {i + 1:2d} PROBE ctx~{ptokens:6d}tok  {'PASS' if ok else 'FAIL'}  "
                  f"reply={reply.strip()[:40]!r}")
        else:
            print(f"  turn {i + 1:2d}       ctx~{ptokens:6d}tok  (filler)")
    return results


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    n_turns = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    print(f"=== BASELINE (rule stated once) - seed {seed}, {n_turns} turns ===")
    base = run_arm(reinject=False, seed=seed, n_turns=n_turns)
    print(f"\n=== ANCHOR (rule re-injected every turn) - seed {seed}, {n_turns} turns ===")
    anc = run_arm(reinject=True, seed=seed, n_turns=n_turns)

    base_flags = [r["complied"] for r in base]
    anc_flags = [r["complied"] for r in anc]

    sys.path.insert(0, "src")
    from anchor.bench import drift_adherence

    out = drift_adherence([], anc_flags, base_flags)
    print("\n=== RESULT ===")
    print(f"  turns: {len(TASKS)}   max ctx (baseline): {max(r['prompt_tokens'] for r in base)} tok")
    print(f"  adherence WITHOUT anchor (baseline): {out['adherence_without']:.0%}")
    print(f"  adherence WITH anchor (re-inject):   {out['adherence_with']:.0%}")
    print(f"  delta:                               {out['delta']:+.0%}")

    # crude adherence-vs-context curve (thirds)
    n = len(base_flags)
    third = max(1, n // 3)
    for label, lo, hi in [("early", 0, third), ("mid", third, 2 * third), ("late", 2 * third, n)]:
        b = base_flags[lo:hi]
        a = anc_flags[lo:hi]
        bf = sum(b) / len(b) if b else 0
        af = sum(a) / len(a) if a else 0
        print(f"  [{label:5s} turns {lo + 1}-{hi}] baseline {bf:.0%}  vs  anchor {af:.0%}")

    with open("benchmarks/drift_live_result.json", "w") as f:
        json.dump({"baseline": base, "anchor": anc, "summary": out}, f, indent=2)
    print("\n  full per-turn data -> benchmarks/drift_live_result.json")


if __name__ == "__main__":
    main()
