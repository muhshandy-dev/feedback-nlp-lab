"""Fine-tuning encoder IndoBERT untuk sentimen 3 kelas.

Dijalankan terpisah dari pipeline utama karena butuh bobot model (Hugging Face) dan sebaiknya GPU
(Kaggle). Keluarannya `reports/encoder_run.json`, yang kemudian dievaluasi oleh
`feedbacklab run` dengan metrik dan test set yang sama persis dengan baseline TF-IDF.

Protokol yang dikunci sebelum dijalankan:
- model `indobenchmark/indobert-base-p1` (MIT) pada revisi tetap, hanya pra-latih (bukan model yang
  sudah di-fine-tune pada SmSA, karena teks NusaX diambil dari SmSA sehingga akan bocor);
- dilatih di train (500), epoch terbaik dipilih dengan macro-F1 validasi (100);
- 3 seed; run final = seed dengan macro-F1 validasi tertinggi. Test hanya diprediksi sekali per seed
  sesudah epoch terkunci, dan skor test semua seed dilaporkan supaya variansinya terlihat.
"""

from __future__ import annotations

import json
import platform
import time
from pathlib import Path

import numpy as np

from .data import LABELS, load
from .metrics import macro_f1

MODEL_ID = "indobenchmark/indobert-base-p1"
MODEL_REVISION = "c2cd0b51ddce6580eb35263b39b0a1e5fb0a39e2"
SEEDS = (11, 22, 33)
CONFIG = {
    "max_length": 128,
    "batch_size": 16,
    "learning_rate": 2e-5,
    "weight_decay": 0.01,
    "epochs": 8,
    "warmup_ratio": 0.1,
}


def _trim(batch):
    """Potong padding di luar token terpanjang dalam batch. Hasil model sama (padding sudah
    di-mask), tetapi di CPU jauh lebih cepat karena ulasan rata-rata hanya sekitar 40 token."""
    n = int(batch["attention_mask"].sum(dim=1).max())
    return {k: v[:, :n] for k, v in batch.items()}


def _batches(enc, labels, batch_size, shuffle, rng):
    idx = np.arange(len(labels))
    if shuffle:
        rng.shuffle(idx)
    for start in range(0, len(idx), batch_size):
        sel = idx[start : start + batch_size]
        yield _trim({k: v[sel] for k, v in enc.items()}), labels[sel]


def _predict(model, enc, batch_size, device):
    import torch

    model.eval()
    probs = []
    with torch.no_grad():
        n = enc["input_ids"].shape[0]
        for start in range(0, n, batch_size):
            batch = _trim({k: v[start : start + batch_size] for k, v in enc.items()})
            batch = {k: v.to(device) for k, v in batch.items()}
            probs.append(torch.softmax(model(**batch).logits, dim=-1).cpu().numpy())
    return np.concatenate(probs)


def train_one(seed, splits, tokenizer, model_id, revision, config, device):
    import torch
    from transformers import AutoModelForSequenceClassification, get_linear_schedule_with_warmup

    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    lab2id = {lab: i for i, lab in enumerate(LABELS)}

    def encode(df):
        return dict(
            tokenizer(
                list(df["text"]),
                truncation=True,
                max_length=config["max_length"],
                padding="max_length",
                return_tensors="pt",
            )
        )

    enc = {name: encode(df) for name, df in splits.items()}
    y = {name: torch.tensor([lab2id[v] for v in df["label"]]) for name, df in splits.items()}

    model = AutoModelForSequenceClassification.from_pretrained(
        model_id, revision=revision, num_labels=len(LABELS)
    ).to(device)
    opt = torch.optim.AdamW(
        model.parameters(), lr=config["learning_rate"], weight_decay=config["weight_decay"]
    )
    steps = config["epochs"] * int(np.ceil(len(y["train"]) / config["batch_size"]))
    sched = get_linear_schedule_with_warmup(opt, int(config["warmup_ratio"] * steps), steps)

    curve, best_state, best_f1 = [], None, -1.0
    for epoch in range(1, config["epochs"] + 1):
        model.train()
        losses = []
        for batch, labels in _batches(enc["train"], y["train"], config["batch_size"], True, rng):
            batch = {k: v.to(device) for k, v in batch.items()}
            out = model(**batch, labels=labels.to(device))
            out.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad()
            losses.append(out.loss.item())
        pv = _predict(model, enc["valid"], 64, device)
        f1 = macro_f1(splits["valid"]["label"], [LABELS[i] for i in pv.argmax(1)], LABELS)
        curve.append({"epoch": epoch, "train_loss": float(np.mean(losses)), "valid_macro_f1": f1})
        if f1 > best_f1:
            best_f1 = f1
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)
    best_epoch = max(curve, key=lambda c: (c["valid_macro_f1"], -c["epoch"]))["epoch"]
    test_probs = _predict(model, enc["test"], 64, device)
    valid_probs = _predict(model, enc["valid"], 64, device)
    return {
        "seed": seed,
        "curve": curve,
        "best_epoch": best_epoch,
        "valid_macro_f1": best_f1,
        "test_macro_f1": macro_f1(
            splits["test"]["label"], [LABELS[i] for i in test_probs.argmax(1)], LABELS
        ),
        "test_probs": test_probs.round(6).tolist(),
        "valid_probs": valid_probs.round(6).tolist(),
    }


def _runner() -> dict:
    """Asal eksekusi, supaya hasil tidak bisa diklaim berasal dari tempat lain."""
    import os

    if os.environ.get("GITHUB_RUN_ID"):
        return {
            "platform": "github-actions",
            "repository": os.environ.get("GITHUB_REPOSITORY"),
            "run_id": os.environ["GITHUB_RUN_ID"],
            "sha": os.environ.get("GITHUB_SHA"),
        }
    if os.environ.get("KAGGLE_KERNEL_RUN_TYPE"):
        return {"platform": "kaggle", "run_type": os.environ["KAGGLE_KERNEL_RUN_TYPE"]}
    return {"platform": "lokal", "host": platform.node()}


def run(
    out_path: Path,
    data_dir=None,
    model_id=MODEL_ID,
    revision=MODEL_REVISION,
    config=None,
    seeds=SEEDS,
) -> dict:
    import torch
    import transformers
    from transformers import AutoTokenizer

    config = {**CONFIG, **(config or {})}
    splits = load(data_dir) if data_dir else load()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
    started = time.time()
    runs = [train_one(s, splits, tokenizer, model_id, revision, config, device) for s in seeds]
    best = max(runs, key=lambda r: (r["valid_macro_f1"], -r["seed"]))
    result = {
        "model_id": model_id,
        "revision": revision,
        "config": config,
        "labels": list(LABELS),
        "test_ids": splits["test"]["id"].tolist(),
        "valid_ids": splits["valid"]["id"].tolist(),
        "selected_seed": best["seed"],
        "runs": runs,
        "environment": {
            "device": device,
            "gpu": torch.cuda.get_device_name(0) if device == "cuda" else None,
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "python": platform.python_version(),
            "seconds": round(time.time() - started, 1),
            "runner": _runner(),
        },
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(result), encoding="utf-8")
    return result
