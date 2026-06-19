from anchor.bench import drift_adherence


def test_drift_metric_computation():
    out = drift_adherence(
        rules=[],
        transcript_with_anchor=[True, True, True, True],
        transcript_without=[True, False, False, False],
    )
    assert out["adherence_with"] == 1.0
    assert out["adherence_without"] == 0.25
    assert round(out["delta"], 2) == 0.75
