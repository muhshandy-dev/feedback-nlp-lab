"""Pemeriksaan independen angka yang dipublikasikan website.

Tidak memakai kode pipeline: label asli dibaca langsung dari CSV NusaX, prediksi dari
web/public/data/test_predictions.json, lalu metrik dihitung ulang dengan scikit-learn.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "public" / "data"
LABELS = ["negative", "neutral", "positive"]
errors: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        errors.append(msg)


manifest = json.loads((ROOT / "data" / "nusax_manifest.json").read_text())
raw = ROOT / "data" / "raw" / "nusax" / "test.csv"
check(hashlib.sha256(raw.read_bytes()).hexdigest() == manifest["files"]["test"], "checksum test")
truth = pd.read_csv(raw).set_index("id")["label"]

results = json.loads((WEB / "results.json").read_text())
preds = json.loads((WEB / "test_predictions.json").read_text())
check(
    json.loads((ROOT / "reports" / "results.json").read_text()) == results,
    "reports/results.json berbeda dengan salinan web",
)

rows = preds["rows"]
check(len(rows) == 400 and len({r["id"] for r in rows}) == 400, "jumlah ulasan uji bukan 400")
check(all(truth[r["id"]] == r["label"] for r in rows), "label web != CSV asli")

models = ["tfidf"] + (["encoder"] if results["encoder"]["status"] == "dijalankan" else [])
for m in models:
    y = [truth[r["id"]] for r in rows]
    p = [r[m] for r in rows]
    rep = results[m]["test"]
    f1 = f1_score(y, p, labels=LABELS, average="macro")
    check(abs(f1 - rep["macro_f1"]) < 1e-6, f"{m}: macro-F1 {f1} != {rep['macro_f1']}")
    check(abs(accuracy_score(y, p) - rep["accuracy"]) < 1e-6, f"{m}: akurasi")
    check(confusion_matrix(y, p, labels=LABELS).tolist() == rep["confusion"], f"{m}: confusion")
    lo, hi = rep["macro_f1_ci95"]
    check(lo <= f1 <= hi, f"{m}: macro-F1 di luar CI-nya sendiri")
    probs = [r[f"{m}_probs"] for r in rows]
    check(all(abs(sum(q) - 1) < 1e-4 for q in probs), f"{m}: probabilitas tidak berjumlah 1")
    top = [LABELS[q.index(max(q))] for q in probs]
    check(top == p, f"{m}: argmax probabilitas tidak sama dengan label prediksi")

grid_keys = {k for g in results["tfidf"]["grid"] for k in g}
check(not any("test" in k for k in grid_keys), "grid pemilihan memuat skor test")
check(results["encoder"]["status"] in {"dijalankan", "belum_dijalankan"}, "status encoder")
t = results["topics"]
check(sum(x["size"] for x in t["topics"]) + t["unassigned"] == 1000, "ukuran topik tidak 1000")

if errors:
    print("GAGAL:\n- " + "\n- ".join(errors))
    sys.exit(1)
print(f"OK: {len(models)} model, 400 ulasan uji, angka website cocok dengan perhitungan ulang")
