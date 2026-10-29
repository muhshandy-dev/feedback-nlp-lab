"""Baseline TF-IDF + regresi logistik.

Hyperparameter dipilih dengan 5-fold stratified cross-validation di train saja (validasi resmi hanya
100 ulasan, terlalu bising untuk memilih di antara 21 konfigurasi). Skor validasi tetap dilaporkan.
Test tidak disentuh sampai model final terkunci."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import FeatureUnion, Pipeline

from .data import LABELS
from .metrics import macro_f1
from .text import normalize

FEATURE_SETS = ("word", "char", "word+char")
C_GRID = (0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0)
SEED = 13


def _word() -> TfidfVectorizer:
    return TfidfVectorizer(
        preprocessor=normalize,
        token_pattern=r"(?u)\b\w\w+\b",
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
        dtype=np.float64,
    )


def _char() -> TfidfVectorizer:
    return TfidfVectorizer(
        preprocessor=normalize,
        analyzer="char_wb",
        ngram_range=(2, 5),
        min_df=2,
        sublinear_tf=True,
        dtype=np.float64,
    )


def build(features: str, C: float) -> Pipeline:
    parts = {"word": [("word", _word())], "char": [("char", _char())]}
    parts["word+char"] = parts["word"] + parts["char"]
    clf = LogisticRegression(C=C, class_weight="balanced", max_iter=5000, random_state=SEED)
    return Pipeline([("tfidf", FeatureUnion(parts[features])), ("clf", clf)])


@dataclass
class Selection:
    features: str
    C: float
    cv_macro_f1: float
    valid_macro_f1: float
    grid: list[dict]


def select(train, valid) -> Selection:
    """Pilih konfigurasi dengan CV macro-F1 tertinggi; seri diputus ke model paling sederhana."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    grid = []
    for features, C in product(FEATURE_SETS, C_GRID):
        pred = cross_val_predict(build(features, C), train["text"], train["label"], cv=cv)
        model = build(features, C).fit(train["text"], train["label"])
        grid.append(
            {
                "features": features,
                "C": C,
                "cv_macro_f1": macro_f1(train["label"], pred, LABELS),
                "valid_macro_f1": macro_f1(valid["label"], model.predict(valid["text"]), LABELS),
            }
        )
    best = max(
        grid,
        key=lambda g: (
            round(g["cv_macro_f1"], 6),
            -FEATURE_SETS.index(g["features"]),
            -C_GRID.index(g["C"]),
        ),
    )
    return Selection(best["features"], best["C"], best["cv_macro_f1"], best["valid_macro_f1"], grid)


def majority(train) -> DummyClassifier:
    return DummyClassifier(strategy="most_frequent").fit(train[["text"]], train["label"])
