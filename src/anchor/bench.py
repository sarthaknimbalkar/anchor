import time
from anchor import guard


def drift_adherence(rules, transcript_with_anchor, transcript_without) -> dict:
    def frac(xs):
        return (sum(1 for x in xs if x) / len(xs)) if xs else 0.0

    aw = frac(transcript_with_anchor)
    awo = frac(transcript_without)
    base_violations = sum(1 for x in transcript_without if not x)
    with_violations = sum(1 for x in transcript_with_anchor if not x)
    caught = max(0, base_violations - with_violations)
    bcr = (caught / base_violations) if base_violations else 0.0
    return {
        "adherence_with": aw,
        "adherence_without": awo,
        "block_catch_rate": bcr,
        "delta": aw - awo,
    }


def measure_guard(index, samples: int = 2000) -> dict:
    call = {"tool_name": "Edit", "tool_input": {"file_path": "/p/app.py"}, "cwd": "/p"}
    guard._index_for = lambda cwd: index  # type: ignore[assignment]
    times = []
    for _ in range(samples):
        t0 = time.perf_counter()
        guard.evaluate(call)
        times.append((time.perf_counter() - t0) * 1000.0)
    times.sort()

    def pct(p):
        return times[min(len(times) - 1, int(len(times) * p))]

    return {"p50_ms": pct(0.50), "p95_ms": pct(0.95), "p99_ms": pct(0.99)}
