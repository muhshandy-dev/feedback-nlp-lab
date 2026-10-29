from feedbacklab.text import normalize, tokens


def test_normalize_matches_browser_rules():
    assert normalize("  Enak BANGET!!! harga: Rp15.000  ") == "enak banget harga rp15 000"
    assert normalize("[URL] café") == "url caf"


def test_tokens_drop_single_letters():
    assert tokens("a ok b 4g x") == ["ok", "4g"]
