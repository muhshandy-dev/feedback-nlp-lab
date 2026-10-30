"""Metrik klasifikasi dan uji beda berpasangan."""

from __future__ import annotations

import numpy as np
from scipy.stats import binomtest
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support

BOOTSTRAP_SEED = 20261029
N_BOOT = 2000


def macro_f1(y_true, y_pred, labels) -> float:
    return float(f1_score(y_true, y_pred, labels=list(labels), average="macro", zero_division=0))


def report(y_true, y_pred, labels) -> dict:
    """Macro-F1 dengan 95% CI bootstrap, akurasi, metrik per kelas, dan confusion matrix."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    p, r, f, s = precision_recall_fscore_support(
        y_true, y_pred, labels=list(labels), zero_division=0
    )
    lo, hi = bootstrap_ci(y_true, y_pred, labels)
    return {
        "n": int(len(y_true)),
        "macro_f1": macro_f1(y_true, y_pred, labels),
        "macro_f1_ci95": [lo, hi],
        "accuracy": float((y_true == y_pred).mean()),
        "per_class": {
            lab: {
                "precision": float(p[i]),
                "recall": float(r[i]),
                "f1": float(f[i]),
                "support": int(s[i]),
            }
            for i, lab in enumerate(labels)
        },
        # baris = label asli, kolom = prediksi, urutan mengikuti `labels`
        "confusion": confusion_matrix(y_true, y_pred, labels=list(labels)).tolist(),
    }


def _boot_indices(n: int, n_boot: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, n, size=(n_boot, n))


def bootstrap_ci(y_true, y_pred, labels, n_boot=N_BOOT, seed=BOOTSTRAP_SEED):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    stats = [
        macro_f1(y_true[i], y_pred[i], labels) for i in _boot_indices(len(y_true), n_boot, seed)
    ]
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def paired_comparison(y_true, pred_a, pred_b, labels, n_boot=N_BOOT, seed=BOOTSTRAP_SEED) -> dict:
    """Selisih macro-F1 (b - a) dengan bootstrap berpasangan, plus uji McNemar eksak."""
    y_true = np.asarray(y_true)
    pred_a = np.asarray(pred_a)
    pred_b = np.asarray(pred_b)
    diffs = np.array(
        [
            macro_f1(y_true[i], pred_b[i], labels) - macro_f1(y_true[i], pred_a[i], labels)
            for i in _boot_indices(len(y_true), n_boot, seed)
        ]
    )
    a_ok = pred_a == y_true
    b_ok = pred_b == y_true
    only_a = int((a_ok & ~b_ok).sum())
    only_b = int((~a_ok & b_ok).sum())
    discordant = only_a + only_b
    p_mcnemar = float(binomtest(only_a, discordant, 0.5).pvalue) if discordant else 1.0
    return {
        "delta_macro_f1": macro_f1(y_true, pred_b, labels) - macro_f1(y_true, pred_a, labels),
        "delta_ci95": [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))],
        "p_b_not_better": float((diffs <= 0).mean()),
        "mcnemar": {"only_a_correct": only_a, "only_b_correct": only_b, "p_value": p_mcnemar},
    }
