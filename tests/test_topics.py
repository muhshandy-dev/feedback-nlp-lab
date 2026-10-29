from feedbacklab import topics


def test_npmi_perfect_and_disjoint():
    docs = [{"a", "b"}, {"a", "b"}, {"c", "d"}, {"c", "d"}]
    assert topics.npmi([["a", "b"]], docs) == [1.0]
    assert topics.npmi([["a", "c"]], docs) == [-1.0]


def test_npmi_independent_is_zero():
    docs = [{"a", "b"}, {"a"}, {"b"}, set()]
    assert abs(topics.npmi([["a", "b"]], docs)[0]) < 1e-9


def test_stability_and_diversity():
    run = [["a", "b"], ["c", "d"]]
    assert topics.stability([run, run[::-1]]) == 1.0
    assert topics.diversity(run) == 1.0
    assert topics.diversity([["a", "b"], ["a", "b"]]) == 0.5


def test_choose_k_respects_stability_floor():
    grid = [
        {"k": 4, "npmi_heldout": 0.1, "stability": 0.4},
        {"k": 5, "npmi_heldout": 0.05, "stability": 0.8},
    ]
    assert topics.choose_k(grid) == 5


def test_tokenizer_drops_stopwords_and_numbers():
    assert topics._tokenize("Yang enak itu 2023 ayam goreng di sini ya") == [
        "enak",
        "ayam",
        "goreng",
        "sini",
    ]
