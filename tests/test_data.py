import pytest

from feedbacklab import data


def test_manifest_pinned():
    m = data.manifest()
    assert len(m["commit"]) == 40
    assert m["license"] == "CC-BY-SA-4.0"
    assert set(m["files"]) == set(data.SPLITS)


def test_checksum_mismatch_raises(tmp_path):
    for s in data.SPLITS:
        (tmp_path / f"{s}.csv").write_text("id,text,label\n1,x,positive\n")
    with pytest.raises(ValueError, match="checksum"):
        data.verify(tmp_path)


def test_cross_split_duplicate_detected():
    import pandas as pd

    a = pd.DataFrame({"text": ["Sama Persis"]})
    b = pd.DataFrame({"text": ["sama persis "]})
    with pytest.raises(ValueError, match="duplikat"):
        data._check_disjoint({"train": a, "test": b})
