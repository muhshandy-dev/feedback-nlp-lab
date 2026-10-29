from feedbacklab.keywords import log_odds


def test_distinctive_words_rank_first():
    texts = ["enak sekali"] * 40 + ["buruk sekali"] * 40
    labels = ["positive"] * 40 + ["negative"] * 40
    out = log_odds(texts, labels, ("negative", "positive"), min_count=1)
    assert out["positive"][0]["word"] == "enak"
    assert out["negative"][0]["word"] == "buruk"
    assert out["positive"][0]["z"] > 1.96
    shared = [w for w in out["positive"] if w["word"] == "sekali"][0]
    assert abs(shared["z"]) < 1e-9
