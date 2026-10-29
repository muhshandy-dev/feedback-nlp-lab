"""Uji jalur kode fine-tuning dengan BERT mini acak, tanpa unduh bobot. Bukan uji kualitas."""

import json

import pytest

from feedbacklab import data

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")

needs_data = pytest.mark.skipif(
    not (data.DEFAULT_DATA_DIR / "test.csv").exists(), reason="data NusaX belum diunduh"
)


def _tiny_model(path):
    from collections import Counter

    from transformers import BertConfig, BertForSequenceClassification, BertTokenizerFast

    from feedbacklab.text import tokens

    words = Counter(w for t in data.load()["train"]["text"] for w in tokens(t))
    special = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"]
    (path / "vocab.txt").write_text("\n".join(special + [w for w, _ in words.most_common(800)]))
    BertTokenizerFast(vocab_file=str(path / "vocab.txt"), do_lower_case=True).save_pretrained(path)
    cfg = BertConfig(
        vocab_size=805,
        hidden_size=32,
        num_hidden_layers=1,
        num_attention_heads=2,
        intermediate_size=64,
        max_position_embeddings=64,
        num_labels=3,
    )
    BertForSequenceClassification(cfg).save_pretrained(path)


@pytest.mark.realdata
@needs_data
def test_encoder_run_end_to_end(tmp_path):
    from feedbacklab.encoder import run

    model_dir = tmp_path / "tiny"
    model_dir.mkdir()
    _tiny_model(model_dir)
    out = tmp_path / "encoder_run.json"
    res = run(
        out,
        model_id=str(model_dir),
        revision=None,
        config={"epochs": 2, "max_length": 32, "batch_size": 32},
        seeds=(1, 2),
    )
    saved = json.loads(out.read_text())
    assert saved["selected_seed"] in (1, 2)
    assert len(saved["test_ids"]) == 400
    for r in res["runs"]:
        assert len(r["test_probs"]) == 400 and len(r["valid_probs"]) == 100
        assert len(r["curve"]) == 2
        assert 1 <= r["best_epoch"] <= 2
        assert abs(sum(r["test_probs"][0]) - 1) < 1e-4


@pytest.mark.realdata
@needs_data
def test_pipeline_reads_encoder_run(tmp_path, monkeypatch):
    """Begitu encoder_run.json ada, evaluasi encoder dan uji beda vs TF-IDF ikut terisi."""
    from feedbacklab import pipeline
    from feedbacklab.encoder import run

    model_dir = tmp_path / "tiny"
    model_dir.mkdir()
    _tiny_model(model_dir)
    out = tmp_path / "encoder_run.json"
    run(
        out,
        model_id=str(model_dir),
        revision=None,
        config={"epochs": 1, "max_length": 32, "batch_size": 32},
        seeds=(1,),
    )
    monkeypatch.setattr(pipeline, "ENCODER_RUN", out)
    r = pipeline.run(write=False)
    enc = r["encoder"]
    assert enc["status"] == "dijalankan"
    assert sum(map(sum, enc["test"]["confusion"])) == 400
    assert set(enc["vs_tfidf"]) == {"delta_macro_f1", "delta_ci95", "p_b_not_better", "mcnemar"}
