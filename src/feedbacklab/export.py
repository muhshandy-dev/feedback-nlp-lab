"""Ekspor hasil dan model TF-IDF ke JSON statis untuk website.

Model diekspor lengkap (kosakata, idf, koefisien) supaya browser bisa menghitung ulang prediksi
tanpa server. Paritasnya dengan scikit-learn diuji di `web/tests/model.test.js`.
"""

from __future__ import annotations

import json
from pathlib import Path

from .data import LABELS, ROOT

WEB_DATA = ROOT / "web" / "public" / "data"


def model_json(model, sel) -> dict:
    union = model.named_steps["tfidf"]
    clf = model.named_steps["clf"]
    order = [list(clf.classes_).index(lab) for lab in LABELS]
    analyzers = []
    for name, vec in union.transformer_list:
        vocab = sorted(vec.vocabulary_.items(), key=lambda kv: kv[1])
        analyzers.append(
            {
                "name": name,
                "analyzer": "char_wb" if vec.analyzer == "char_wb" else "word",
                "ngram_range": list(vec.ngram_range),
                "sublinear_tf": bool(vec.sublinear_tf),
                "terms": [t for t, _ in vocab],
                "idf": [round(float(x), 8) for x in vec.idf_],
            }
        )
    return {
        "format": "feedbacklab-tfidf-logreg/1",
        "selected": {"features": sel.features, "C": sel.C},
        "labels": list(LABELS),
        "analyzers": analyzers,
        "coef": [[round(float(x), 8) for x in clf.coef_[i]] for i in order],
        "intercept": [round(float(clf.intercept_[i]), 8) for i in order],
    }


def export_web(model, sel, results: dict, predictions: dict, out_dir: Path = WEB_DATA) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "results.json": results,
        "test_predictions.json": predictions,
        "model.json": model_json(model, sel),
    }
    for name, obj in files.items():
        (out_dir / name).write_text(
            json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n", "utf-8"
        )
