"""Topic modeling NMF di atas TF-IDF, dengan konsistensi topik yang diukur dua cara.

1. Koherensi NPMI pada dokumen held-out: NMF dilatih pada train+valid, NPMI pasangan kata top-10
   dihitung dari ko-okurensi dokumen di test. Topik yang hanya hafal korpus latih mendapat
   skor rendah.
2. Stabilitas antar seed: NMF diulang dengan 5 seed, topik dipasangkan dengan algoritma Hungaria
   berdasarkan Jaccard kata top-10, lalu dirata-rata.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer

from .text import STOPWORDS, tokens

K_GRID = tuple(range(4, 13))
SEEDS = (0, 1, 2, 3, 4)
TOP_N = 10


def _tokenize(text: str) -> list[str]:
    return [t for t in tokens(text) if t not in STOPWORDS and not t.isdigit() and len(t) >= 3]


def vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        tokenizer=_tokenize,
        preprocessor=None,
        lowercase=False,
        token_pattern=None,
        min_df=3,
        max_df=0.5,
        sublinear_tf=True,
    )


def fit_nmf(X, k: int, seed: int) -> NMF:
    return NMF(n_components=k, init="random", random_state=seed, max_iter=2000).fit(X)


def top_words(model: NMF, vocab: np.ndarray, n: int = TOP_N) -> list[list[str]]:
    return [list(vocab[np.argsort(-row)[:n]]) for row in model.components_]


def npmi(topics: list[list[str]], docs: list[set[str]], eps: float = 1e-12) -> list[float]:
    """NPMI rata-rata semua pasangan kata per topik, dari kehadiran kata per dokumen."""
    out = []
    for words in topics:
        occ = {w: np.array([w in d for d in docs]) for w in words}
        scores = []
        for a, b in combinations(words, 2):
            pa, pb = occ[a].mean(), occ[b].mean()
            pab = (occ[a] & occ[b]).mean()
            if pab == 0 or pa == 0 or pb == 0:
                scores.append(-1.0)  # tak pernah muncul bersama di held-out: skor terburuk
                continue
            if pab >= 1 - eps:
                scores.append(1.0)
                continue
            scores.append(float(np.log(pab / (pa * pb)) / -np.log(pab)))
        out.append(float(np.mean(scores)))
    return out


def _jaccard(a: list[str], b: list[str]) -> float:
    return len(set(a) & set(b)) / len(set(a) | set(b))


def stability(runs: list[list[list[str]]]) -> float:
    """Rata-rata Jaccard topik yang dipasangkan optimal, untuk semua pasangan run."""
    vals = []
    for r1, r2 in combinations(runs, 2):
        sim = np.array([[_jaccard(a, b) for b in r2] for a in r1])
        rows, cols = linear_sum_assignment(-sim)
        vals.append(float(sim[rows, cols].mean()))
    return float(np.mean(vals))


def diversity(topics: list[list[str]]) -> float:
    """Proporsi kata unik di seluruh kata top-N (1 berarti tidak ada topik yang tumpang tindih)."""
    words = [w for t in topics for w in t]
    return len(set(words)) / len(words)


def random_baseline(vocab: np.ndarray, k: int, docs: list[set[str]], repeats: int = 20) -> float:
    """NPMI held-out untuk topik berisi kata acak dari kosakata yang sama (batas bawah)."""
    rng = np.random.default_rng(7)
    vals = []
    for _ in range(repeats):
        topics = [list(rng.choice(vocab, size=TOP_N, replace=False)) for _ in range(k)]
        vals.append(float(np.mean(npmi(topics, docs))))
    return float(np.mean(vals))


def sweep(fit_texts: list[str], heldout_texts: list[str]) -> dict:
    vec = vectorizer()
    X = vec.fit_transform(fit_texts)
    vocab = vec.get_feature_names_out()
    docs = [set(_tokenize(t)) for t in heldout_texts]
    rows = []
    for k in K_GRID:
        runs = [top_words(fit_nmf(X, k, s), vocab) for s in SEEDS]
        coh = npmi(runs[0], docs)
        rows.append(
            {
                "k": k,
                "npmi_heldout": float(np.mean(coh)),
                "npmi_random": random_baseline(vocab, k, docs),
                "stability": stability(runs),
                "diversity": diversity(runs[0]),
            }
        )
    return {"vectorizer": vec, "X": X, "vocab": vocab, "grid": rows}


def choose_k(grid: list[dict]) -> int:
    """k dengan NPMI held-out tertinggi di antara k yang stabilitasnya minimal 0,5."""
    ok = [g for g in grid if g["stability"] >= 0.5] or grid
    return max(ok, key=lambda g: (round(g["npmi_heldout"], 6), -g["k"]))["k"]
