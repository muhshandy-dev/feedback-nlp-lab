"""Pipeline lengkap: data, baseline, topik, kata kunci, evaluasi, dan ekspor hasil untuk website."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from . import baseline, keywords, topics
from .data import LABELS, ROOT, load, manifest
from .metrics import paired_comparison, report

REPORTS = ROOT / "reports"
ENCODER_RUN = REPORTS / "encoder_run.json"


def _r(x, nd=6):
    """Pembulatan rekursif supaya JSON stabil byte demi byte antar-run."""
    if isinstance(x, float):
        return round(x, nd)
    if isinstance(x, dict):
        return {k: _r(v, nd) for k, v in x.items()}
    if isinstance(x, list | tuple):
        return [_r(v, nd) for v in x]
    if isinstance(x, np.floating):
        return round(float(x), nd)
    if isinstance(x, np.integer):
        return int(x)
    return x


def _pii_summary(splits) -> dict:
    out = {}
    for name, df in splits.items():
        c = Counter()
        for counts in df["pii"]:
            c.update(counts)
        out[name] = {"documents_with_pii": int(sum(bool(x) for x in df["pii"])), **dict(c)}
    return out


def _errors(test: pd.DataFrame, pred, probs, limit_per_pair: int = 6) -> list[dict]:
    """Kesalahan paling yakin per pasangan (label asli, prediksi)."""
    df = test.assign(pred=pred, conf=probs.max(1))
    rows = []
    for (t, p), g in df[df["label"] != df["pred"]].groupby(["label", "pred"]):
        for _, r in (
            g.sort_values(["conf", "id"], ascending=[False, True]).head(limit_per_pair).iterrows()
        ):
            rows.append(
                {"id": int(r["id"]), "text": r["text"], "label": t, "pred": p, "conf": r["conf"]}
            )
    return rows


def _encoder_section(test: pd.DataFrame, tfidf_pred) -> dict:
    if not ENCODER_RUN.exists():
        return {
            "status": "belum_dijalankan",
            "reason": "Bobot IndoBERT belum bisa diunduh dari lingkungan pembuatan. Kode "
            "fine-tuning dan notebook Kaggle sudah siap; angka akan muncul setelah benar-benar "
            "dijalankan.",
        }
    run = json.loads(ENCODER_RUN.read_text(encoding="utf-8"))
    if run["test_ids"] != test["id"].tolist() or run["labels"] != list(LABELS):
        raise ValueError("encoder_run.json tidak cocok dengan urutan test atau label")
    sel = next(r for r in run["runs"] if r["seed"] == run["selected_seed"])
    probs = np.asarray(sel["test_probs"])
    pred = [LABELS[i] for i in probs.argmax(1)]
    return {
        "status": "dijalankan",
        "model_id": run["model_id"],
        "revision": run["revision"],
        "config": run["config"],
        "environment": run["environment"],
        "selected_seed": run["selected_seed"],
        "seeds": [
            {k: r[k] for k in ("seed", "best_epoch", "valid_macro_f1", "test_macro_f1", "curve")}
            for r in run["runs"]
        ],
        "test": report(test["label"], pred, LABELS),
        "vs_tfidf": paired_comparison(test["label"], tfidf_pred, pred, LABELS),
        "_pred": pred,
        "_probs": probs,
    }


def _topic_section(splits) -> tuple[dict, list[int]]:
    fit_df = pd.concat([splits["train"], splits["valid"]], ignore_index=True)
    all_df = pd.concat([fit_df, splits["test"]], ignore_index=True)
    sw = topics.sweep(list(fit_df["text"]), list(splits["test"]["text"]))
    k = topics.choose_k(sw["grid"])
    model = topics.fit_nmf(sw["X"], k, topics.SEEDS[0])
    vocab = sw["vocab"]
    heldout_docs = [set(topics._tokenize(t)) for t in splits["test"]["text"]]
    words = topics.top_words(model, vocab)
    per_topic_npmi = topics.npmi(words, heldout_docs)

    W = model.transform(sw["vectorizer"].transform(all_df["text"]))
    assigned = [int(np.argmax(row)) if row.max() > 0 else -1 for row in W]
    items = []
    for t in range(k):
        mask = np.array(assigned) == t
        mix = Counter(all_df.loc[mask, "label"])
        comp = model.components_[t]
        order = np.argsort(-comp)[: topics.TOP_N]
        top_docs = np.argsort(-W[:, t])[:3]
        items.append(
            {
                "id": t,
                "words": [
                    {"word": vocab[i], "weight": float(comp[i] / comp[order[0]])} for i in order
                ],
                "npmi_heldout": per_topic_npmi[t],
                "size": int(mask.sum()),
                "sentiment": {lab: int(mix.get(lab, 0)) for lab in LABELS},
                "examples": [all_df.loc[i, "text"] for i in top_docs],
            }
        )
    section = {
        "method": "NMF di atas TF-IDF kata (kata henti dibuang), dilatih pada train+valid",
        "k": k,
        "k_rule": "NPMI held-out tertinggi di antara k dengan stabilitas >= 0,5",
        "grid": sw["grid"],
        "unassigned": int(sum(a == -1 for a in assigned)),
        "topics": items,
    }
    return section, assigned


def run(write: bool = True) -> dict:
    splits = load()
    train, valid, test = splits["train"], splits["valid"], splits["test"]

    maj = baseline.majority(train)
    maj_pred = maj.predict(test[["text"]])

    sel = baseline.select(train, valid)
    model = baseline.build(sel.features, sel.C).fit(train["text"], train["label"])
    tf_valid = model.predict(valid["text"])
    tf_probs = model.predict_proba(test["text"])
    classes = list(model.classes_)
    tf_probs = tf_probs[:, [classes.index(lab) for lab in LABELS]]
    tf_pred = [LABELS[i] for i in tf_probs.argmax(1)]

    enc = _encoder_section(test, tf_pred)
    topic_section, assigned = _topic_section(splits)
    all_df = pd.concat([train, valid, test], ignore_index=True)

    results = {
        "dataset": {
            **{k: manifest()[k] for k in ("dataset", "repo", "commit", "license", "citation")},
            "sizes": {name: len(df) for name, df in splits.items()},
            "label_counts": {
                name: {lab: int((df["label"] == lab).sum()) for lab in LABELS}
                for name, df in splits.items()
            },
            "pii_removed": _pii_summary(splits),
        },
        "labels": list(LABELS),
        "majority": {"predicts": str(maj_pred[0]), "test": report(test["label"], maj_pred, LABELS)},
        "tfidf": {
            "selected": {"features": sel.features, "C": sel.C},
            "cv_macro_f1": sel.cv_macro_f1,
            "grid": sel.grid,
            "valid": report(valid["label"], tf_valid, LABELS),
            "test": report(test["label"], tf_pred, LABELS),
            "vs_majority": paired_comparison(test["label"], maj_pred, tf_pred, LABELS),
            "errors": _errors(test, tf_pred, tf_probs),
        },
        "encoder": {k: v for k, v in enc.items() if not k.startswith("_")},
        "topics": topic_section,
        "keywords": keywords.log_odds(all_df["text"], all_df["label"], LABELS),
    }
    if "_pred" in enc:
        results["encoder"]["errors"] = _errors(test, enc["_pred"], enc["_probs"])

    predictions = {
        "labels": list(LABELS),
        "rows": [
            {
                "id": int(r.id),
                "text": r.text,
                "label": r.label,
                "tfidf": tf_pred[i],
                "tfidf_probs": tf_probs[i].tolist(),
                **(
                    {"encoder": enc["_pred"][i], "encoder_probs": enc["_probs"][i].tolist()}
                    if "_pred" in enc
                    else {}
                ),
                "topic": assigned[len(train) + len(valid) + i],
            }
            for i, r in enumerate(test.itertuples())
        ],
    }
    results = _r(results)
    predictions = _r(predictions)
    if write:
        REPORTS.mkdir(exist_ok=True)
        _dump(REPORTS / "results.json", results)
        _dump(REPORTS / "test_predictions.json", predictions)
        from .export import export_web

        export_web(model, sel, results, predictions)
    return results


def _dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False) + "\n", "utf-8")
