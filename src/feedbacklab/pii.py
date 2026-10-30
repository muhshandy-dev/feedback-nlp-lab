"""Penghapusan data pribadi dari teks ulasan sebelum dipakai model atau ditampilkan."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Urutan penting: URL dan email lebih dulu agar mention dan angka di dalamnya
# tidak dihitung dua kali.
PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("url", re.compile(r"\bhttps?://\S+|\bwww\.\S+", re.IGNORECASE), "[URL]"),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"), "[EMAIL]"),
    ("mention", re.compile(r"(?<![\w@])@\w{2,}"), "[AKUN]"),
    # Nomor HP Indonesia: 08xx, +628xx, 628xx, boleh dipisah spasi, titik, atau strip.
    (
        "phone",
        re.compile(r"(?<!\d)(?:\+62[\s.-]?|62[\s.-]?|0)8\d{1,3}(?:[\s.-]?\d{2,4}){2,4}(?!\d)"),
        "[TELEPON]",
    ),
    # NIK, nomor rekening, nomor kartu: deretan 10 digit atau lebih.
    ("long_number", re.compile(r"(?<!\d)\d{10,}(?!\d)"), "[NOMOR]"),
)


@dataclass(frozen=True)
class Scrubbed:
    text: str
    counts: dict[str, int] = field(default_factory=dict)


def scrub(text: str) -> Scrubbed:
    counts: dict[str, int] = {}
    for name, pattern, token in PATTERNS:
        text, n = pattern.subn(token, text)
        if n:
            counts[name] = n
    return Scrubbed(text=text, counts=counts)
