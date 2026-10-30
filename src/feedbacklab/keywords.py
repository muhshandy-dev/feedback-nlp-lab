"""Kata kunci per sentimen dengan weighted log-odds ratio berprior Dirichlet (Monroe dkk., 2008).

Lebih jujur daripada frekuensi mentah: kata umum yang sering muncul di semua kelas tidak naik
ke atas, dan kata langka tidak meledak karena prior menyusutkan perkiraannya. Skor z > 1,96
kira-kira berarti kata itu lebih khas untuk kelas tersebut dibanding kelas lain pada taraf 5%.
"""

from __future__ import annotations

from collections import Counter

import numpy as np

from .text import tokens

# Kata fungsi murni dibuang, tapi kata negasi dan penguat sengaja dipertahankan.
_DROP = frozenset(
    "yang dan di ke dari ini itu untuk dengan ada saya kami kita aku dia mereka akan juga pada "
    "atau karena jadi sudah bisa dalam saja lagi ya nya kalau sama buat oleh se para pun "
    "lah kah".split()
)


def log_odds(texts, labels, classes, top: int = 15, min_count: int = 3, alpha0: float = 500.0):
    counts = {c: Counter() for c in classes}
    for t, lab in zip(texts, labels, strict=True):
        counts[lab].update(w for w in tokens(t) if w not in _DROP and not w.isdigit())
    total = Counter()
    for c in classes:
        total.update(counts[c])
    vocab = sorted(w for w, n in total.items() if n >= min_count)
    prior_total = sum(total[w] for w in vocab)
    alpha = {w: alpha0 * total[w] / prior_total for w in vocab}
    out = {}
    for c in classes:
        rest = Counter()
        for o in classes:
            if o != c:
                rest.update(counts[o])
        n_c = sum(counts[c][w] for w in vocab)
        n_r = sum(rest[w] for w in vocab)
        rows = []
        for w in vocab:
            a = alpha[w]
            yc, yr = counts[c][w], rest[w]
            delta = np.log((yc + a) / (n_c + alpha0 - yc - a)) - np.log(
                (yr + a) / (n_r + alpha0 - yr - a)
            )
            var = 1.0 / (yc + a) + 1.0 / (yr + a)
            rows.append((w, float(delta / np.sqrt(var)), int(yc)))
        rows.sort(key=lambda r: (-r[1], r[0]))
        out[c] = [{"word": w, "z": round(z, 4), "count": n} for w, z, n in rows[:top]]
    return out
