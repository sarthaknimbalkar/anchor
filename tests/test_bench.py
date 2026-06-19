from anchor.bench import measure_guard
from anchor.rules import Rule, TIER_BLOCK
from anchor.compile import compile_match
from anchor.cache import index_by_tool


def test_measure_returns_percentiles():
    idx = index_by_tool(
        [Rule(id="e", tier=TIER_BLOCK, text="t", match=compile_match({"protects_paths": ["**/.env"]}))]
    )
    out = measure_guard(idx, samples=200)
    assert out["p95_ms"] >= out["p50_ms"] >= 0
