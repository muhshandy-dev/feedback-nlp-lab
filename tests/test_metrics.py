import numpy as np

from feedbacklab.metrics import paired_comparison, report

L = ("negative", "neutral", "positive")


def test_perfect_report():
    y = ["negative", "neutral", "positive"] * 10
    r = report(y, y, L)
    assert r["macro_f1"] == 1.0
    assert r["macro_f1_ci95"] == [1.0, 1.0]
    assert r["confusion"] == [[10, 0, 0], [0, 10, 0], [0, 0, 10]]


def test_confusion_orientation_rows_are_truth():
    r = report(["negative", "negative"], ["positive", "negative"], L)
    assert r["confusion"][0] == [1, 0, 1]


def test_paired_identical_models():
    rng = np.random.default_rng(0)
    y = list(rng.choice(L, 200))
    p = list(rng.choice(L, 200))
    c = paired_comparison(y, p, p, L)
    assert c["delta_macro_f1"] == 0
    assert c["mcnemar"]["p_value"] == 1.0


def test_paired_better_model_detected():
    rng = np.random.default_rng(1)
    y = np.array(rng.choice(L, 300))
    bad = np.array(rng.choice(L, 300))
    good = y.copy()
    good[:30] = bad[:30]
    c = paired_comparison(y, bad, good, L)
    assert c["delta_ci95"][0] > 0
    assert c["mcnemar"]["p_value"] < 0.001
