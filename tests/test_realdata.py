"""Tes pada data NusaX asli. Butuh `feedbacklab data fetch` lebih dulu."""

import json

import pytest

from feedbacklab import data

pytestmark = pytest.mark.realdata

needs_data = pytest.mark.skipif(
    not (data.DEFAULT_DATA_DIR / "test.csv").exists(), reason="data NusaX belum diunduh"
)


@needs_data
def test_splits_official_sizes_and_disjoint():
    s = data.load()
    assert {k: len(v) for k, v in s.items()} == {"train": 500, "valid": 100, "test": 400}
    ids = [set(v["id"]) for v in s.values()]
    assert all(len(v) == n for v, n in zip(ids, (500, 100, 400), strict=True))


@needs_data
def test_pipeline_reproduces_committed_results_exactly():
    from feedbacklab.pipeline import REPORTS, run

    committed = (REPORTS / "results.json").read_text(encoding="utf-8")
    fresh = run(write=False)
    assert fresh == json.loads(committed)


@needs_data
def test_test_split_not_used_for_selection():
    """Grid hanya memuat skor CV train dan validasi, tidak ada skor test."""
    r = json.loads((data.ROOT / "reports" / "results.json").read_text(encoding="utf-8"))
    for g in r["tfidf"]["grid"]:
        assert set(g) == {"features", "C", "cv_macro_f1", "valid_macro_f1"}
    best = max(r["tfidf"]["grid"], key=lambda g: g["cv_macro_f1"])
    assert (best["features"], best["C"]) == (
        r["tfidf"]["selected"]["features"],
        r["tfidf"]["selected"]["C"],
    )
